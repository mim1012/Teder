"""
2024년 4월-7월 실제 USDT/KRW 데이터를 사용한 백테스트 실행 스크립트
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 콘솔 인코딩 설정 (Windows 환경)
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_loader import load_april_july_2024_data, DataValidator
from backtest_engine import run_quick_backtest, BacktestConfig
from performance_analyzer import analyze_backtest_performance
from report_generator import generate_backtest_report
import matplotlib.pyplot as plt

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_historical_backtest(
    initial_balance: float = 1000000,
    limit_order_fee: float = 0.0000,
    market_order_fee: float = 0.0002,
    slippage_rate: float = 0.0001,
    save_reports: bool = True
):
    """
    2024년 4월-7월 실제 데이터를 사용한 백테스트 실행
    
    Args:
        initial_balance: 초기 자금
        limit_order_fee: 지정가 수수료율 (0%)
        market_order_fee: 시장가 수수료율 (0.02%)
        slippage_rate: 슬리피지율
        save_reports: 리포트 저장 여부
    """
    
    print("=" * 80)
    print("USDT/KRW 2024년 4-7월 실제 데이터 백테스트")
    print("=" * 80)
    
    try:
        # 1. 실제 과거 데이터 로드
        print(f"\n[데이터 로드] 2024년 4-7월 실제 USDT/KRW 데이터 로드 중...")
        data = load_april_july_2024_data()
        
        # 데이터 검증
        is_valid, errors = DataValidator.validate_ohlcv_data(data)
        if not is_valid:
            print(f"[경고] 데이터 검증 오류: {errors}")
            print("그래도 백테스트를 계속 진행합니다...")
        
        print(f"[완료] 실제 데이터 로드 완료: {len(data)}개 캔들")
        print(f"   기간: {data['timestamp'].min()} ~ {data['timestamp'].max()}")
        print(f"   가격 범위: {data['close'].min():.2f} ~ {data['close'].max():.2f}원")
        
        # 데이터 통계
        total_days = (data['timestamp'].max() - data['timestamp'].min()).days + 1
        print(f"   총 기간: {total_days}일")
        print(f"   평균 거래량: {data['volume'].mean():,.0f}")
        print(f"   가격 변동성: {(data['close'].std() / data['close'].mean() * 100):.2f}%")
        
        # 월별 통계
        data['month'] = data['timestamp'].dt.month
        monthly_stats = data.groupby('month')['close'].agg(['mean', 'min', 'max', 'count'])
        print(f"\n   월별 가격 통계:")
        for month, stats in monthly_stats.iterrows():
            print(f"     {month}월: 평균 {stats['mean']:.0f}원, 범위 {stats['min']:.0f}-{stats['max']:.0f}원, {stats['count']}시간")
        
        # 2. 백테스트 설정
        print(f"\n[설정] 백테스트 설정")
        config = BacktestConfig(
            initial_balance=initial_balance,
            limit_order_fee=limit_order_fee,
            market_order_fee=market_order_fee,
            slippage_rate=slippage_rate
        )
        
        print(f"   초기 자금: {initial_balance:,.0f}원")
        print(f"   지정가 수수료: {limit_order_fee*100:.2f}%")
        print(f"   시장가 수수료: {market_order_fee*100:.2f}%")
        print(f"   슬리피지: {slippage_rate*100:.3f}%")
        
        # 3. 백테스트 실행
        print(f"\n[실행] 백테스트 실행 중...")
        print(f"   - RSI(14) 3봉/5봉 기울기 조건 검증")
        print(f"   - EMA(20) 3봉(≥0.3)/5봉(≥0.2) 기울기 조건 검증")
        print(f"   - 매도1호가 매수, +4원 익절 전략")
        
        backtest_result = run_quick_backtest(data, config)
        
        # 4. 성과 분석
        print(f"\n[분석] 성과 분석 중...")
        analysis_result = analyze_backtest_performance(backtest_result)
        
        # 5. 결과 출력
        print_detailed_results(backtest_result, analysis_result, data)
        
        # 6. 리포트 생성
        if save_reports:
            print(f"\n[리포트] 리포트 생성 중...")
            generate_and_save_reports(backtest_result, analysis_result, "historical_2024_apr_jul")
        
        # 7. 차트 표시
        print(f"\n[차트] 차트 생성 중...")
        chart_fig, text_report = generate_backtest_report(backtest_result, analysis_result)
        
        return backtest_result, analysis_result, chart_fig, text_report
        
    except Exception as e:
        logger.error(f"백테스트 실행 실패: {e}")
        raise


def print_detailed_results(backtest_result, analysis_result, data):
    """상세한 백테스트 결과 출력"""
    
    print("\n" + "=" * 60)
    print("2024년 4-7월 USDT/KRW 백테스트 결과")
    print("=" * 60)
    
    metrics = analysis_result.get('metrics', {})
    trades = backtest_result.get('trades', [])
    
    # 기본 지표
    print(f"\n== 기본 성과 지표 ==")
    print(f"- 총 수익률: {metrics.get('total_return_pct', 0):.2f}%")
    print(f"- 절대 수익: {metrics.get('total_return_abs', 0):,.0f}원")
    print(f"- 최종 자산: {backtest_result.get('final_balance', 0):,.0f}원")
    print(f"- 총 거래 수: {metrics.get('total_trades', 0)}회")
    
    # 거래 성과
    print(f"\n== 거래 성과 ==")
    print(f"- 승률: {metrics.get('win_rate_pct', 0):.1f}%")
    print(f"- 승리 거래: {metrics.get('winning_trades', 0)}회")
    print(f"- 패배 거래: {metrics.get('losing_trades', 0)}회")
    print(f"- 수익 팩터: {metrics.get('profit_factor', 0):.2f}")
    print(f"- 평균 수익: {metrics.get('avg_win', 0):,.0f}원")
    print(f"- 평균 손실: {metrics.get('avg_loss', 0):,.0f}원")
    print(f"- 최대 연속 승리: {metrics.get('max_consecutive_wins', 0)}회")
    print(f"- 최대 연속 패배: {metrics.get('max_consecutive_losses', 0)}회")
    
    # 위험 지표
    print(f"\n== 위험 지표 ==")
    print(f"- 최대 낙폭: {metrics.get('max_drawdown_pct', 0):.2f}%")
    print(f"- 샤프 비율: {metrics.get('sharpe_ratio', 0):.2f}")
    print(f"- 소르티노 비율: {metrics.get('sortino_ratio', 0):.2f}")
    print(f"- 칼마 비율: {metrics.get('calmar_ratio', 0):.2f}")
    print(f"- 연간 변동성: {metrics.get('volatility_annual_pct', 0):.2f}%")
    
    # 거래 패턴
    print(f"\n== 거래 패턴 ==")
    print(f"- 평균 보유시간: {metrics.get('avg_holding_hours', 0):.1f}시간")
    print(f"- 최대 보유시간: {metrics.get('max_holding_hours', 0):.1f}시간")
    print(f"- 최소 보유시간: {metrics.get('min_holding_hours', 0):.1f}시간")
    
    # 매도 이유 분석
    if trades:
        reasons = {}
        for trade in trades:
            reason = trade.reason or '기타'
            reasons[reason] = reasons.get(reason, 0) + 1
        
        print(f"\n== 매도 이유별 분포 ==")
        for reason, count in reasons.items():
            pct = (count / len(trades)) * 100
            print(f"- {reason}: {count}회 ({pct:.1f}%)")
    
    # 월별 성과
    if trades:
        monthly_performance = {}
        for trade in trades:
            if hasattr(trade, 'buy_time') and trade.buy_time:
                month = trade.buy_time.month
                if month not in monthly_performance:
                    monthly_performance[month] = {'trades': 0, 'profit': 0, 'wins': 0}
                monthly_performance[month]['trades'] += 1
                monthly_performance[month]['profit'] += trade.profit
                if trade.profit > 0:
                    monthly_performance[month]['wins'] += 1
        
        if monthly_performance:
            print(f"\n== 월별 거래 성과 ==")
            for month in sorted(monthly_performance.keys()):
                stats = monthly_performance[month]
                win_rate = (stats['wins'] / stats['trades']) * 100 if stats['trades'] > 0 else 0
                print(f"- {month}월: {stats['trades']}회 거래, {stats['profit']:+,.0f}원, 승률 {win_rate:.1f}%")
    
    # 바이앤드홀드 비교
    comparison = analysis_result.get('buy_hold_comparison', {})
    if comparison:
        print(f"\n== 바이앤드홀드 비교 ==")
        print(f"- 전략 수익률: {comparison.get('strategy_return_pct', 0):.2f}%")
        print(f"- 바이앤드홀드 수익률: {comparison.get('buy_hold_return_pct', 0):.2f}%")
        print(f"- 초과 수익률: {comparison.get('outperformance_pct', 0):.2f}%p")
    
    # 시장 환경 분석
    print(f"\n== 시장 환경 분석 ==")
    market_return = ((data['close'].iloc[-1] / data['close'].iloc[0]) - 1) * 100
    total_volatility = data['close'].pct_change().std() * (24**0.5) * 100  # 일일 변동성
    
    print(f"- 기간 내 시장 수익률: {market_return:.2f}%")
    print(f"- 일일 평균 변동성: {total_volatility:.2f}%")
    print(f"- 총 거래일: {len(data) // 24}일")
    
    # 전략 평가
    print(f"\n== 전략 평가 ==")
    evaluate_historical_performance(metrics, comparison, market_return)


def evaluate_historical_performance(metrics, comparison, market_return):
    """실제 데이터 기반 전략 성과 평가"""
    
    total_return = metrics.get('total_return_pct', 0)
    win_rate = metrics.get('win_rate_pct', 0)
    sharpe_ratio = metrics.get('sharpe_ratio', 0)
    max_dd = metrics.get('max_drawdown_pct', 0)
    profit_factor = metrics.get('profit_factor', 0)
    total_trades = metrics.get('total_trades', 0)
    
    # 실제 데이터 기반 종합 점수 계산
    score = 0
    
    # 수익률 점수 (30점) - 4개월 기준으로 조정
    monthly_return = total_return / 4  # 월 평균 수익률
    if monthly_return > 5:
        score += 30
    elif monthly_return > 3:
        score += 25
    elif monthly_return > 1:
        score += 20
    elif monthly_return > 0:
        score += 10
    elif monthly_return > -2:
        score += 5
    
    # 승률 점수 (20점)  
    if win_rate > 60:
        score += 20
    elif win_rate > 50:
        score += 15
    elif win_rate > 40:
        score += 10
    elif win_rate > 30:
        score += 5
    
    # 샤프 비율 점수 (20점)
    if sharpe_ratio > 1.5:
        score += 20
    elif sharpe_ratio > 1:
        score += 15
    elif sharpe_ratio > 0.5:
        score += 10
    elif sharpe_ratio > 0:
        score += 5
    
    # 최대 낙폭 점수 (15점, 역점수)
    if max_dd < 3:
        score += 15
    elif max_dd < 5:
        score += 12
    elif max_dd < 8:
        score += 8
    elif max_dd < 12:
        score += 4
    
    # 거래 빈도 점수 (15점)
    if 20 <= total_trades <= 100:  # 적절한 거래 빈도
        score += 15
    elif 10 <= total_trades <= 150:
        score += 10
    elif 5 <= total_trades <= 200:
        score += 5
    
    # 등급 평가
    if score >= 80:
        grade = "A (우수)"
        comment = "실제 데이터에서 매우 우수한 성과입니다. 실전 투자 가능성이 높습니다."
    elif score >= 65:
        grade = "B (양호)"
        comment = "실제 데이터에서 양호한 성과입니다. 추가 최적화 후 실전 검토 가능합니다."
    elif score >= 45:
        grade = "C (보통)"
        comment = "실제 데이터에서 보통 수준의 성과입니다. 전략 개선이 필요합니다."
    elif score >= 25:
        grade = "D (미흡)"
        comment = "실제 데이터에서 미흡한 성과입니다. 전략을 재검토해야 합니다."
    else:
        grade = "F (부진)"
        comment = "실제 데이터에서 부진한 성과입니다. 전략을 대폭 수정해야 합니다."
    
    print(f"- 종합 등급: {grade} (점수: {score}/100)")
    print(f"- 평가 의견: {comment}")
    
    # 시장 대비 성과
    outperformance = total_return - market_return
    if outperformance > 5:
        market_comment = "시장을 크게 아웃퍼폼했습니다."
    elif outperformance > 2:
        market_comment = "시장을 소폭 아웃퍼폼했습니다."
    elif outperformance > -2:
        market_comment = "시장과 비슷한 성과를 보였습니다."
    else:
        market_comment = "시장을 언더퍼폼했습니다."
    
    print(f"- 시장 대비 성과: {outperformance:+.2f}%p ({market_comment})")
    
    # 실제 데이터 기반 개선 제안
    suggestions = []
    
    if win_rate < 45:
        suggestions.append("실제 시장에서 승률이 낮습니다. 매수 조건을 더 엄격하게 설정하세요.")
    
    if max_dd > 8:
        suggestions.append("실제 시장에서 손실 위험이 큽니다. 손절 로직을 강화하세요.")
    
    if profit_factor < 1.2:
        suggestions.append("수익/손실 비율이 낮습니다. 익절/손절 비율을 조정하세요.")
    
    if total_trades < 10:
        suggestions.append("거래 기회가 너무 적습니다. 매수 조건을 완화해보세요.")
    elif total_trades > 150:
        suggestions.append("과도하게 많은 거래가 발생했습니다. 매수 조건을 강화해보세요.")
    
    if sharpe_ratio < 0.8:
        suggestions.append("위험 대비 수익률이 낮습니다. 리스크 관리를 강화하세요.")
    
    if outperformance < -1:
        suggestions.append("단순 보유 전략보다 못한 성과입니다. 전략의 근본적 재검토가 필요합니다.")
    
    if suggestions:
        print(f"\n== 실제 데이터 기반 개선 제안 ==")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")


def generate_and_save_reports(backtest_result, analysis_result, prefix="historical"):
    """리포트 생성 및 저장"""
    
    # 현재 시간으로 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 저장 디렉토리 생성
    report_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(report_dir, exist_ok=True)
    
    # 파일 경로
    chart_path = os.path.join(report_dir, f"{prefix}_backtest_chart_{timestamp}.png")
    summary_path = os.path.join(report_dir, f"{prefix}_backtest_summary_{timestamp}.txt")
    
    try:
        # 리포트 생성 및 저장
        chart_fig, text_report = generate_backtest_report(
            backtest_result,
            analysis_result,
            save_chart_path=chart_path,
            save_summary_path=summary_path
        )
        
        print(f"[완료] 리포트 저장 완료:")
        print(f"   차트: {chart_path}")
        print(f"   요약: {summary_path}")
        
        return chart_path, summary_path
        
    except Exception as e:
        logger.error(f"리포트 저장 실패: {e}")
        return None, None


if __name__ == "__main__":
    print("USDT/KRW 2024년 4-7월 실제 데이터 백테스트 시스템")
    print("=" * 60)
    
    # 실제 과거 데이터 백테스트 실행
    try:
        result = run_historical_backtest(
            initial_balance=1000000,
            limit_order_fee=0.0000,    # 코인원 지정가 수수료 0%
            market_order_fee=0.0002,   # 코인원 시장가 수수료 0.02%
            slippage_rate=0.0001,      # 0.01% 슬리피지
            save_reports=True
        )
        
        # 차트 표시 (CLI에서는 비활성화)
        # plt.show()
        print("[차트] 차트가 생성되었습니다. GUI 환경에서 확인 가능합니다.")
        
    except Exception as e:
        logger.error(f"백테스트 실행 실패: {e}")
    
    print(f"\n[완료] 2024년 4-7월 실제 데이터 백테스트 완료!")
    print(f"[정보] 이 결과는 실제 시장 데이터를 바탕으로 한 것입니다.")
    print(f"[주의] 과거 성과가 미래 수익을 보장하지는 않습니다.")