"""
통합 백테스트 실행 스크립트
전체 백테스트 프로세스를 실행하고 결과를 출력
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

from data_loader import load_backtest_data, load_april_july_2024_data, SampleDataGenerator
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


def run_comprehensive_backtest(
    use_real_data: bool = False,
    days: int = 30,
    initial_balance: float = 1000000,
    limit_order_fee: float = 0.0000,
    market_order_fee: float = 0.0002,
    slippage_rate: float = 0.0001,
    save_reports: bool = True
):
    """
    종합 백테스트 실행
    
    Args:
        use_real_data: 실제 API 데이터 사용 여부
        days: 백테스트 기간 (일수)
        initial_balance: 초기 자금
        limit_order_fee: 지정가 수수료율 (0%)
        market_order_fee: 시장가 수수료율 (0.02%)
        slippage_rate: 슬리피지율
        save_reports: 리포트 저장 여부
    """
    
    print("=" * 80)
    print("USDT/KRW 자동매매 전략 백테스트 시작")
    print("=" * 80)
    
    try:
        # 1. 데이터 로드
        print(f"\n[데이터 로드] {'실제 데이터' if use_real_data else '샘플 데이터'} 로드 중...")
        data = load_backtest_data(
            use_real_data=use_real_data,
            days=days,
            currency="usdt"
        )
        
        print(f"[완료] 데이터 로드 완료: {len(data)}개 캔들")
        print(f"   기간: {data['timestamp'].min()} ~ {data['timestamp'].max()}")
        print(f"   가격 범위: {data['close'].min():.2f} ~ {data['close'].max():.2f}원")
        
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
        backtest_result = run_quick_backtest(data, config)
        
        # 4. 성과 분석
        print(f"\n[분석] 성과 분석 중...")
        analysis_result = analyze_backtest_performance(backtest_result)
        
        # 5. 결과 출력
        print_backtest_results(backtest_result, analysis_result)
        
        # 6. 리포트 생성
        if save_reports:
            print(f"\n[리포트] 리포트 생성 중...")
            generate_and_save_reports(backtest_result, analysis_result)
        
        # 7. 차트 표시
        print(f"\n[차트] 차트 생성 중...")
        chart_fig, text_report = generate_backtest_report(backtest_result, analysis_result)
        
        return backtest_result, analysis_result, chart_fig, text_report
        
    except Exception as e:
        logger.error(f"백테스트 실행 실패: {e}")
        raise


def print_backtest_results(backtest_result, analysis_result):
    """백테스트 결과 출력"""
    
    print("\n" + "=" * 60)
    print("백테스트 결과 요약")
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
    
    # 바이앤드홀드 비교
    comparison = analysis_result.get('buy_hold_comparison', {})
    if comparison:
        print(f"\n== 바이앤드홀드 비교 ==")
        print(f"- 전략 수익률: {comparison.get('strategy_return_pct', 0):.2f}%")
        print(f"- 바이앤드홀드 수익률: {comparison.get('buy_hold_return_pct', 0):.2f}%")
        print(f"- 초과 수익률: {comparison.get('outperformance_pct', 0):.2f}%p")
    
    # 전략 평가
    print(f"\n== 전략 평가 ==")
    evaluate_strategy_performance(metrics, comparison)


def evaluate_strategy_performance(metrics, comparison):
    """전략 성과 평가"""
    
    total_return = metrics.get('total_return_pct', 0)
    win_rate = metrics.get('win_rate_pct', 0)
    sharpe_ratio = metrics.get('sharpe_ratio', 0)
    max_dd = metrics.get('max_drawdown_pct', 0)
    profit_factor = metrics.get('profit_factor', 0)
    
    # 종합 점수 계산
    score = 0
    
    # 수익률 점수 (40점)
    if total_return > 20:
        score += 40
    elif total_return > 10:
        score += 30
    elif total_return > 5:
        score += 20
    elif total_return > 0:
        score += 10
    
    # 승률 점수 (20점)  
    if win_rate > 70:
        score += 20
    elif win_rate > 60:
        score += 15
    elif win_rate > 50:
        score += 10
    elif win_rate > 40:
        score += 5
    
    # 샤프 비율 점수 (20점)
    if sharpe_ratio > 2:
        score += 20
    elif sharpe_ratio > 1:
        score += 15
    elif sharpe_ratio > 0.5:
        score += 10
    elif sharpe_ratio > 0:
        score += 5
    
    # 최대 낙폭 점수 (20점, 역점수)
    if max_dd < 5:
        score += 20
    elif max_dd < 10:
        score += 15
    elif max_dd < 15:
        score += 10
    elif max_dd < 25:
        score += 5
    
    # 등급 평가
    if score >= 80:
        grade = "A (우수)"
        comment = "매우 우수한 성과입니다. 실전 투자를 고려할 수 있습니다."
    elif score >= 60:
        grade = "B (양호)"
        comment = "양호한 성과입니다. 추가 최적화 후 실전 검토 가능합니다."
    elif score >= 40:
        grade = "C (보통)"
        comment = "보통 수준의 성과입니다. 전략 개선이 필요합니다."
    else:
        grade = "D (부진)"
        comment = "부진한 성과입니다. 전략을 재검토해야 합니다."
    
    print(f"- 종합 등급: {grade} (점수: {score}/100)")
    print(f"- 평가 의견: {comment}")
    
    # 개선 제안
    suggestions = []
    
    if win_rate < 50:
        suggestions.append("승률 개선을 위한 진입 조건 강화 필요")
    
    if max_dd > 15:
        suggestions.append("리스크 관리 강화 (손절 로직 개선)")
    
    if profit_factor < 1.5:
        suggestions.append("수익/손실 비율 개선 필요")
    
    if sharpe_ratio < 1:
        suggestions.append("위험 대비 수익률 개선 필요")
    
    if suggestions:
        print(f"\n== 개선 제안 ==")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")


def generate_and_save_reports(backtest_result, analysis_result):
    """리포트 생성 및 저장"""
    
    # 현재 시간으로 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 저장 디렉토리 생성
    report_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(report_dir, exist_ok=True)
    
    # 파일 경로
    chart_path = os.path.join(report_dir, f"backtest_chart_{timestamp}.png")
    summary_path = os.path.join(report_dir, f"backtest_summary_{timestamp}.txt")
    
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


def run_multiple_backtests(scenarios: list):
    """여러 시나리오 백테스트"""
    
    print("\n" + "=" * 80)
    print("다중 시나리오 백테스트")
    print("=" * 80)
    
    results = []
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[시나리오 {i}] {scenario['name']}")
        print("-" * 50)
        
        try:
            result = run_comprehensive_backtest(**scenario['params'])
            results.append({
                'name': scenario['name'],
                'result': result
            })
            
        except Exception as e:
            logger.error(f"시나리오 {i} 실행 실패: {e}")
    
    # 시나리오 비교
    if len(results) > 1:
        print("\n" + "=" * 60)
        print("시나리오 비교")
        print("=" * 60)
        
        for result in results:
            name = result['name']
            analysis = result['result'][1]  # analysis_result
            metrics = analysis.get('metrics', {})
            
            print(f"\n{name}:")
            print(f"  • 총 수익률: {metrics.get('total_return_pct', 0):.2f}%")
            print(f"  • 승률: {metrics.get('win_rate_pct', 0):.1f}%")
            print(f"  • 샤프 비율: {metrics.get('sharpe_ratio', 0):.2f}")
            print(f"  • 최대 낙폭: {metrics.get('max_drawdown_pct', 0):.2f}%")
    
    return results


if __name__ == "__main__":
    print("USDT/KRW 자동매매 백테스트 시스템")
    print("=" * 60)
    
    # 기본 백테스트 실행
    try:
        result = run_comprehensive_backtest(
            use_real_data=True,  # 실제 API 데이터 사용
            days=30,
            initial_balance=1000000,
            save_reports=True
        )
        
        # 차트 표시 (CLI에서는 비활성화)
        # plt.show()
        print("[차트] 차트가 생성되었습니다. GUI 환경에서 확인 가능합니다.")
        
    except Exception as e:
        logger.error(f"백테스트 실행 실패: {e}")
    
    # 다중 시나리오 테스트 (선택사항)
    # run_scenarios = input("\n다중 시나리오 테스트를 실행하시겠습니까? (y/n): ").lower()
    run_scenarios = 'n'  # 자동으로 n으로 설정
    
    if run_scenarios == 'y':
        scenarios = [
            {
                'name': '기본 전략',
                'params': {
                    'use_real_data': False,
                    'days': 30,
                    'initial_balance': 1000000,
                    'limit_order_fee': 0.0000,
                    'market_order_fee': 0.0002,
                    'save_reports': False
                }
            },
            {
                'name': '수수료 높음',
                'params': {
                    'use_real_data': False,
                    'days': 30,
                    'initial_balance': 1000000,
                    'limit_order_fee': 0.0000,
                    'market_order_fee': 0.003,  # 0.3%
                    'save_reports': False
                }
            },
            {
                'name': '장기 테스트',
                'params': {
                    'use_real_data': False,
                    'days': 90,
                    'initial_balance': 1000000,
                    'limit_order_fee': 0.0000,
                    'market_order_fee': 0.0002,
                    'save_reports': False
                }
            }
        ]
        
        run_multiple_backtests(scenarios)
    
    print(f"\n[완료] 백테스트 완료!")