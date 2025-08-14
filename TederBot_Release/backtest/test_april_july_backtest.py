"""
2024년 4월-7월 USDT/KRW 데이터를 사용한 백테스트 테스트
"""

import os
import sys
import logging
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_loader import load_april_july_2024_data, DataValidator
from backtest_engine import run_quick_backtest, BacktestConfig
from performance_analyzer import analyze_backtest_performance
from report_generator import generate_backtest_report

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("2024년 4월-7월 USDT/KRW 백테스트 테스트")
    print("=" * 50)
    
    try:
        # 1. 데이터 로드
        print("1. 과거 데이터 로드 중...")
        df = load_april_july_2024_data()
        
        if df.empty:
            print("[FAIL] 데이터 로드 실패")
            return
        
        print(f"[OK] 데이터 로드 완료: {len(df)}개 레코드")
        print(f"   - 기간: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
        print(f"   - 가격 범위: {df['close'].min():.2f} ~ {df['close'].max():.2f} KRW")
        
        # 2. 데이터 유효성 검증
        print("\n2. 데이터 유효성 검증...")
        is_valid, errors = DataValidator.validate_ohlcv_data(df)
        
        if not is_valid:
            print(f"[FAIL] 데이터 검증 실패: {errors}")
            return
        
        print("[OK] 데이터 검증 통과")
        
        # 3. 백테스트 설정
        print("\n3. 백테스트 실행...")
        config = BacktestConfig(
            initial_balance=1000000,    # 100만원 시작
            limit_order_fee=0.0000,     # 지정가 수수료 0% (코인원)
            market_order_fee=0.0002,    # 시장가 수수료 0.02% (코인원)
            slippage_rate=0.0001        # 슬리피지 0.01%
        )
        
        # 4. 백테스트 실행
        results = run_quick_backtest(df, config)
        
        if not results:
            print("[FAIL] 백테스트 실행 실패")
            return
        
        print("[OK] 백테스트 실행 완료")
        
        # 5. 성과 분석
        print("\n4. 성과 분석 중...")
        performance = analyze_backtest_performance(results)
        
        # 6. 결과 출력
        print("\n" + "="*60)
        print("백테스트 결과 요약")
        print("="*60)
        
        # 기본 정보
        print(f"테스트 기간: {df['timestamp'].min().strftime('%Y-%m-%d')} ~ {df['timestamp'].max().strftime('%Y-%m-%d')}")
        print(f"총 거래일: {len(df) // 24}일")
        print(f"초기 자본: {config.initial_balance:,}원")
        
        # 거래 통계
        trades = results.get('trades', [])
        
        print(f"\n거래 통계:")
        print(f"- 총 거래 횟수: {len(trades)}회")
        
        # 성과 지표
        if performance:
            print(f"\n성과 지표:")
            
            final_balance = performance.get('final_balance', config.initial_balance)
            total_return = (final_balance - config.initial_balance) / config.initial_balance * 100
            
            print(f"- 최종 잔고: {final_balance:,.0f}원")
            print(f"- 총 수익률: {total_return:.2f}%")
            
            if 'max_drawdown' in performance:
                print(f"- 최대 손실: {performance['max_drawdown']:.2f}%")
            
            if 'win_rate' in performance:
                print(f"- 승률: {performance['win_rate']:.1f}%")
            
            if 'sharpe_ratio' in performance:
                print(f"- 샤프 비율: {performance['sharpe_ratio']:.2f}")
        
        # 7. 상세 리포트 생성
        print("\n5. 상세 리포트 생성 중...")
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = generate_backtest_report(
                results, 
                performance, 
                f"2024년 4-7월 USDT/KRW 백테스트_{timestamp}"
            )
            print(f"[OK] 리포트 생성 완료: {report_path}")
        except Exception as e:
            print(f"[WARN] 리포트 생성 실패: {e}")
        
        print("\n" + "="*60)
        print("백테스트 완료!")
        print("="*60)
        
        return results, performance
        
    except Exception as e:
        logger.error(f"백테스트 실행 중 오류: {e}")
        print(f"[ERROR] 오류 발생: {e}")
        return None

if __name__ == "__main__":
    result = main()
    if result:
        print("\n[SUCCESS] 백테스트가 성공적으로 완료되었습니다!")
        print("리포트 파일과 차트를 확인해보세요.")
    else:
        print("\n[FAIL] 백테스트 실행에 실패했습니다.")