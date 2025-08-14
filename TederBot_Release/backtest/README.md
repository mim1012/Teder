# USDT/KRW 자동매매 백테스트 시스템

코인원 API 기반 USDT/KRW 자동매매 전략의 백테스트 시스템입니다.

## 📁 파일 구조

```
backtest/
├── __init__.py                    # 패키지 초기화
├── data_loader.py                 # 과거 데이터 로더
├── backtest_engine.py             # 백테스트 엔진
├── performance_analyzer.py        # 성과 분석 모듈
├── report_generator.py           # 리포트 생성 모듈
├── run_backtest.py               # 통합 실행 스크립트
├── test_backtest_system.py       # 시스템 테스트 스크립트
├── reports/                      # 생성된 리포트 저장
│   ├── backtest_chart_*.png     # 차트 리포트
│   └── backtest_summary_*.txt   # 텍스트 요약
└── README.md                     # 이 파일
```

## 🚀 주요 기능

### 1. 데이터 로더 (data_loader.py)
- **CoinoneDataLoader**: 코인원 API에서 실제 OHLCV 데이터 수집
- **SampleDataGenerator**: 현실적인 가격 움직임의 샘플 데이터 생성
- **DataValidator**: OHLCV 데이터 유효성 검증

### 2. 백테스트 엔진 (backtest_engine.py)
- **TradingStrategy**: RSI/EMA 기반 매매 전략 구현
- **BacktestEngine**: 백테스트 실행 엔진
- **Position/Trade 관리**: 포지션 및 거래 내역 추적

### 3. 성과 분석 (performance_analyzer.py)
- **PerformanceMetrics**: 종합 성과 지표 계산
  - 총 수익률, 승률, 수익 팩터
  - 최대 낙폭(MDD), 샤프 비율, 소르티노 비율
  - 변동성, 칼마 비율, 회복 팩터
- **거래 분포 분석**: 손익 분포 및 패턴 분석
- **바이앤드홀드 비교**: 전략 성과 vs 단순 보유 전략

### 4. 리포트 생성 (report_generator.py)
- **종합 차트 리포트**: 자산 곡선, 가격 차트, 성과 지표 시각화
- **텍스트 요약 리포트**: 핵심 성과 지표 요약
- **다양한 시각화**: matplotlib/seaborn 기반 차트 생성

## 📊 매매 전략 규칙

### 매수 조건 (모두 충족시)
1. **RSI(14) 조건**: 직전 3봉과 5봉의 기울기가 모두 양수
2. **EMA(20) 조건**: 
   - 직전 3봉 기울기 >= 0.3
   - 직전 5봉 기울기 >= 0.2

### 매도 조건 (하나라도 충족시)
1. **익절**: 평균매수가 + 4원
2. **시간 초과**: 매수 후 24시간 경과
3. **RSI 과매수**: RSI(14) > 70
4. **EMA 하락**: 3봉 기울기가 지속적으로 감소

### 거래 방식
- **매수**: 보유 원화 전량, 매도1호가 지정가
- **매도**: 보유 USDT 전량, 시장가
- **수수료**: 0.15%
- **슬리피지**: 0.01%

## 💻 사용 방법

### 1. 기본 백테스트 실행
```bash
cd backtest/
python run_backtest.py
```

### 2. 시스템 테스트
```bash
python test_backtest_system.py
```

### 3. 모듈별 사용 예제
```python
from data_loader import load_backtest_data
from backtest_engine import run_quick_backtest, BacktestConfig
from performance_analyzer import analyze_backtest_performance
from report_generator import generate_backtest_report

# 데이터 로드
data = load_backtest_data(use_real_data=False, days=30)

# 백테스트 설정
config = BacktestConfig(
    initial_balance=1000000,
    fee_rate=0.0015,
    slippage_rate=0.0001
)

# 백테스트 실행
backtest_result = run_quick_backtest(data, config)

# 성과 분석
analysis_result = analyze_backtest_performance(backtest_result)

# 리포트 생성
chart_fig, text_report = generate_backtest_report(
    backtest_result, 
    analysis_result
)
```

## 📈 성과 지표 설명

### 기본 지표
- **총 수익률**: (최종 자산 / 초기 자산 - 1) × 100
- **승률**: 수익 거래 / 전체 거래 × 100
- **수익 팩터**: 총 수익 / 총 손실

### 위험 지표
- **최대 낙폭(MDD)**: 고점 대비 최대 하락률
- **샤프 비율**: (수익률 - 무위험수익률) / 변동성
- **소르티노 비율**: (수익률 - 무위험수익률) / 하향 변동성
- **칼마 비율**: 연간 수익률 / 최대 낙폭

### 거래 분석
- **평균 보유시간**: 포지션 평균 보유 시간
- **기댓값**: 거래당 기대 손익
- **회복 팩터**: 총 수익률 / 최대 낙폭

## 🔧 설정 파라미터

### BacktestConfig 주요 설정
```python
@dataclass
class BacktestConfig:
    initial_balance: float = 1000000.0  # 초기 자금
    fee_rate: float = 0.0015           # 수수료 0.15%
    slippage_rate: float = 0.0001      # 슬리피지 0.01%
    
    # 매수 조건 파라미터
    rsi_period: int = 14               # RSI 기간
    ema_period: int = 20               # EMA 기간
    rsi_slope_periods: List[int] = [3, 5]  # RSI 기울기 계산 기간
    ema_slope_thresholds: List[float] = [0.3, 0.2]  # EMA 기울기 임계값
    
    # 매도 조건 파라미터
    profit_target: float = 4.0         # 익절 목표 (원)
    max_hold_hours: int = 24           # 최대 보유 시간
    rsi_overbought: float = 70.0       # RSI 과매수 기준
```

## 📋 백테스트 결과 예시

```
== 기본 성과 지표 ==
- 총 수익률: -15.48%
- 절대 수익: -154,752원
- 최종 자산: 845,248원
- 총 거래 수: 62회

== 거래 성과 ==
- 승률: 53.2%
- 승리 거래: 33회
- 패배 거래: 29회
- 수익 팩터: 0.78
- 평균 수익: 17,720원
- 평균 손실: -25,700원

== 위험 지표 ==
- 최대 낙폭: 21.58%
- 샤프 비율: -2.52
- 소르티노 비율: -1.88
- 칼마 비율: -4.02
- 연간 변동성: 71.40%

== 전략 평가 ==
- 종합 등급: D (부진) (점수: 15/100)
- 평가 의견: 부진한 성과입니다. 전략을 재검토해야 합니다.
```

## 🎯 개선 방안

현재 백테스트 결과가 부진한 경우 다음 사항을 고려해보세요:

1. **진입 조건 강화**: RSI/EMA 임계값 조정
2. **손절 로직 추가**: 고정 손절가 설정
3. **거래 비용 최적화**: 수수료율 협상
4. **시장 상황별 전략**: 상승/하락/횡보장별 다른 전략
5. **포지션 크기 조절**: 켈리 공식 등을 활용한 자금 관리

## 🔍 테스트 결과

```bash
백테스트 시스템 테스트 결과: 5/5 통과
[SUCCESS] 모든 테스트 통과! 백테스트 시스템이 정상 작동합니다.
```

모든 핵심 모듈이 정상적으로 작동하며, 다양한 시나리오에서 안정적인 백테스트가 가능합니다.

## 📞 문의 및 지원

백테스트 결과 해석이나 전략 개선에 대한 문의는 개발 팀에 연락해주세요.

---

> **주의**: 백테스트 결과는 과거 데이터를 기반으로 하며, 실제 거래 결과와 다를 수 있습니다. 실전 투자 전에 충분한 검증과 리스크 관리가 필요합니다.