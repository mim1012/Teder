"""
백테스트 시스템 테스트 스크립트
각 모듈의 기능을 테스트하고 검증
"""

import sys
import os
import logging
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_loader import SampleDataGenerator, DataValidator, load_backtest_data
from backtest_engine import run_quick_backtest, BacktestConfig
from performance_analyzer import analyze_backtest_performance
from report_generator import generate_backtest_report

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_data_loader():
    """데이터 로더 테스트"""
    print("\n=== 데이터 로더 테스트 ===")
    
    try:
        # 샘플 데이터 생성 테스트
        sample_data = SampleDataGenerator.generate_realistic_data(hours=100)
        print(f"[OK] 샘플 데이터 생성 성공: {len(sample_data)}개 캔들")
        
        # 데이터 유효성 검증 테스트
        is_valid, errors = DataValidator.validate_ohlcv_data(sample_data)
        if is_valid:
            print("[OK] 데이터 유효성 검증 통과")
        else:
            print(f"[FAIL] 데이터 유효성 검증 실패: {errors}")
            return False
        
        # 백테스트용 데이터 로드 테스트
        test_data = load_backtest_data(use_real_data=False, days=5)
        print(f"[OK] 백테스트 데이터 로드 성공: {len(test_data)}개 캔들")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 데이터 로더 테스트 실패: {e}")
        return False


def test_backtest_engine():
    """백테스트 엔진 테스트"""
    print("\n=== 백테스트 엔진 테스트 ===")
    
    try:
        # 테스트 데이터 준비
        test_data = SampleDataGenerator.generate_realistic_data(hours=200)
        
        # 백테스트 설정
        config = BacktestConfig(
            initial_balance=500000,
            fee_rate=0.001,
            slippage_rate=0.0001
        )
        
        # 백테스트 실행
        result = run_quick_backtest(test_data, config)
        
        # 결과 검증
        if 'trades' in result and 'equity_curve' in result:
            print(f"[OK] 백테스트 실행 성공")
            print(f"  - 총 거래 수: {len(result['trades'])}개")
            print(f"  - 최종 잔고: {result['final_balance']:,.0f}원")
            print(f"  - 자산 곡선 데이터 포인트: {len(result['equity_curve'])}개")
            return True
        else:
            print("[FAIL] 백테스트 결과 구조 이상")
            return False
        
    except Exception as e:
        print(f"[FAIL] 백테스트 엔진 테스트 실패: {e}")
        return False


def test_performance_analyzer():
    """성과 분석기 테스트"""
    print("\n=== 성과 분석기 테스트 ===")
    
    try:
        # 백테스트 결과 준비
        test_data = SampleDataGenerator.generate_realistic_data(hours=150)
        config = BacktestConfig(initial_balance=1000000)
        backtest_result = run_quick_backtest(test_data, config)
        
        # 성과 분석 실행
        analysis_result = analyze_backtest_performance(backtest_result)
        
        # 결과 검증
        required_keys = ['metrics', 'trade_distribution', 'drawdown_periods']
        
        for key in required_keys:
            if key not in analysis_result:
                print(f"[FAIL] 분석 결과에 {key} 누락")
                return False
        
        metrics = analysis_result['metrics']
        expected_metrics = [
            'total_return_pct', 'win_rate_pct', 'max_drawdown_pct', 
            'sharpe_ratio', 'total_trades'
        ]
        
        for metric in expected_metrics:
            if metric not in metrics:
                print(f"[FAIL] 성과 지표에 {metric} 누락")
                return False
        
        print("[OK] 성과 분석 실행 성공")
        print(f"  - 총 수익률: {metrics['total_return_pct']:.2f}%")
        print(f"  - 승률: {metrics['win_rate_pct']:.1f}%")
        print(f"  - 샤프 비율: {metrics['sharpe_ratio']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 성과 분석기 테스트 실패: {e}")
        return False


def test_report_generator():
    """리포트 생성기 테스트"""
    print("\n=== 리포트 생성기 테스트 ===")
    
    try:
        # 백테스트 및 분석 결과 준비
        test_data = SampleDataGenerator.generate_realistic_data(hours=300)
        config = BacktestConfig(initial_balance=1000000)
        backtest_result = run_quick_backtest(test_data, config)
        analysis_result = analyze_backtest_performance(backtest_result)
        
        # 리포트 생성 (저장하지 않음)
        chart_fig, text_report = generate_backtest_report(
            backtest_result, 
            analysis_result,
            save_chart_path=None,
            save_summary_path=None
        )
        
        # 결과 검증
        if chart_fig is not None and text_report:
            print("[OK] 리포트 생성 성공")
            print(f"  - 차트 객체 생성: {'성공' if chart_fig else '실패'}")
            print(f"  - 텍스트 리포트 길이: {len(text_report)}자")
            
            # 텍스트 리포트에 필수 내용 포함 확인
            required_content = ['총 수익률', '승률', '최대 낙폭', '샤프 비율']
            missing_content = [content for content in required_content if content not in text_report]
            
            if missing_content:
                print(f"[FAIL] 텍스트 리포트에 필수 내용 누락: {missing_content}")
                return False
            
            return True
        else:
            print("[FAIL] 리포트 생성 결과 이상")
            return False
        
    except Exception as e:
        print(f"[FAIL] 리포트 생성기 테스트 실패: {e}")
        return False


def test_integration():
    """통합 테스트"""
    print("\n=== 통합 테스트 ===")
    
    try:
        # 전체 프로세스 실행
        print("전체 백테스트 프로세스 실행...")
        
        # 1. 데이터 준비
        data = load_backtest_data(use_real_data=False, days=10)
        
        # 2. 백테스트 실행 (여러 시나리오)
        scenarios = [
            {"name": "낮은 수수료", "fee_rate": 0.001},
            {"name": "높은 수수료", "fee_rate": 0.003},
            {"name": "큰 초기자금", "initial_balance": 5000000}
        ]
        
        results = []
        for scenario in scenarios:
            config = BacktestConfig(
                initial_balance=scenario.get("initial_balance", 1000000),
                fee_rate=scenario.get("fee_rate", 0.0015)
            )
            
            backtest_result = run_quick_backtest(data, config)
            analysis_result = analyze_backtest_performance(backtest_result)
            
            results.append({
                'name': scenario['name'],
                'return': analysis_result['metrics']['total_return_pct'],
                'trades': analysis_result['metrics']['total_trades'],
                'win_rate': analysis_result['metrics']['win_rate_pct']
            })
        
        # 결과 출력
        print("[OK] 통합 테스트 성공")
        print("\n시나리오별 결과:")
        for result in results:
            print(f"  {result['name']}: 수익률 {result['return']:.2f}%, "
                  f"거래 {result['trades']}회, 승률 {result['win_rate']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 통합 테스트 실패: {e}")
        return False


def run_all_tests():
    """모든 테스트 실행"""
    print("백테스트 시스템 테스트 시작")
    print("=" * 60)
    
    tests = [
        ("데이터 로더", test_data_loader),
        ("백테스트 엔진", test_backtest_engine),
        ("성과 분석기", test_performance_analyzer),
        ("리포트 생성기", test_report_generator),
        ("통합 테스트", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
            print()
        except Exception as e:
            print(f"[ERROR] {test_name} 테스트 중 예외 발생: {e}")
    
    print("=" * 60)
    print(f"테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("[SUCCESS] 모든 테스트 통과! 백테스트 시스템이 정상 작동합니다.")
        return True
    else:
        print("[WARNING] 일부 테스트 실패. 문제를 확인해주세요.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n백테스트 시스템 사용 방법:")
        print("1. 'python run_backtest.py' - 기본 백테스트 실행")
        print("2. 모듈별로 import하여 사용자 정의 백테스트 구현")
        print("3. reports/ 폴더에서 생성된 차트와 리포트 확인")
    
    sys.exit(0 if success else 1)