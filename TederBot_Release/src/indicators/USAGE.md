# 기술적 지표 모듈 사용법

## 개요

코인원 USDT/KRW 자동매매를 위한 RSI(14)와 EMA(20) 기술적 지표 계산 및 분석 모듈입니다.

## 주요 기능

### 1. RSI(14) 분석
- **매수 조건**: 직전 3봉과 5봉의 기울기가 모두 양수 (0.00 불포함)
- **매도 조건**: 실시간 RSI > 70

### 2. EMA(20) 분석  
- **매수 조건**: 직전 3봉 기울기 >= 0.3, 직전 5봉 기울기 >= 0.2
- **매도 조건**: 직전 3봉 기울기가 지속적으로 감소

### 3. RSI-EMA 복합 분석
- **계산 과정**: RSI(14) 계산 → RSI 값들에 대한 EMA(20) 적용
- **매수 조건**: RSI-EMA 직전 3봉 기울기 >= 0.3, 직전 5봉 기울기 >= 0.2
- **매도 조건**: RSI-EMA 직전 3봉 기울기가 지속적으로 감소

## 기본 사용법

### 데이터 준비

```python
import pandas as pd

# OHLCV 데이터프레임 (필수 컬럼: open, high, low, close, volume)
data = pd.DataFrame({
    'timestamp': [...],  # 시간 정보
    'open': [...],       # 시가
    'high': [...],       # 고가  
    'low': [...],        # 저가
    'close': [...],      # 종가
    'volume': [...]      # 거래량
})
```

### RSI 사용법

```python
from src.indicators import RSICalculator, get_rsi_buy_signal

# 방법 1: RSICalculator 클래스 사용
rsi_calc = RSICalculator(period=14)

# RSI 계산
rsi_series = rsi_calc.calculate_rsi(data)

# 매수 조건 확인
buy_signal, analysis = rsi_calc.check_buy_condition(data)

print(f"RSI 매수 신호: {buy_signal}")
print(f"현재 RSI: {analysis['current_value']:.2f}")
print(f"RSI 기울기: {analysis['slopes']}")

# 방법 2: 편의 함수 사용
buy_signal, analysis = get_rsi_buy_signal(data)
```

### EMA 사용법

```python
from src.indicators import EMACalculator, get_ema_buy_signal

# 방법 1: EMACalculator 클래스 사용
ema_calc = EMACalculator(period=20)

# EMA 계산
ema_series = ema_calc.calculate_ema(data)

# 매수 조건 확인
buy_signal, analysis = ema_calc.check_buy_condition(data)

print(f"EMA 매수 신호: {buy_signal}")
print(f"현재 EMA: {analysis['current_value']:.2f}")
print(f"EMA 기울기: {analysis['slopes']}")
print(f"임계값 확인: {analysis['analysis']['threshold_checks']}")

# 방법 2: 편의 함수 사용
buy_signal, analysis = get_ema_buy_signal(data)
```

### RSI-EMA 사용법

```python
from src.indicators import RSIEMACalculator, get_rsi_ema_buy_signal

# 방법 1: RSIEMACalculator 클래스 사용
rsi_ema_calc = RSIEMACalculator(rsi_period=14, ema_period=20)

# RSI-EMA 계산
rsi_ema_series = rsi_ema_calc.calculate_rsi_ema(data)

# 매수 조건 확인
buy_signal, analysis = rsi_ema_calc.check_buy_condition(data)

print(f"RSI-EMA 매수 신호: {buy_signal}")
print(f"현재 RSI-EMA: {analysis['current_value']:.2f}")
print(f"RSI-EMA 기울기: {analysis['slopes']}")

# 상세 분석
detailed = rsi_ema_calc.get_detailed_analysis(data)
print(f"RSI 값: {detailed['rsi_value']:.2f}")
print(f"RSI-EMA 값: {detailed['rsi_ema_value']:.2f}")
print(f"모멘텀 강도: {detailed['analysis_summary']['momentum_strength']}")
print(f"추세 방향: {detailed['analysis_summary']['trend_direction']}")

# 방법 2: 편의 함수 사용
buy_signal, analysis = get_rsi_ema_buy_signal(data)
```

### 복합 매수 신호

```python
from src.indicators import get_rsi_buy_signal, get_ema_buy_signal, get_rsi_ema_buy_signal

# 각각의 매수 신호 확인
rsi_buy, rsi_analysis = get_rsi_buy_signal(data)
ema_buy, ema_analysis = get_ema_buy_signal(data)
rsi_ema_buy, rsi_ema_analysis = get_rsi_ema_buy_signal(data)

# 복합 매수 신호 (모든 조건 충족)
final_buy_signal = rsi_buy and ema_buy and rsi_ema_buy

print(f"RSI 신호: {rsi_buy}")
print(f"EMA 신호: {ema_buy}")
print(f"RSI-EMA 신호: {rsi_ema_buy}")
print(f"최종 매수 신호: {final_buy_signal}")
```

### 실시간 모니터링

```python
from src.indicators import RSIMonitor, EMAMonitor, RSIEMAMonitor

# 모니터링 객체 생성
rsi_monitor = RSIMonitor(period=14)
ema_monitor = EMAMonitor(period=20)
rsi_ema_monitor = RSIEMAMonitor(rsi_period=14, ema_period=20)

# 현재 상태 조회
rsi_status = rsi_monitor.get_current_status(data)
ema_status = ema_monitor.get_current_status(data)
rsi_ema_status = rsi_ema_monitor.get_current_status(data)

# 상태 메시지 출력
print(f"RSI: {rsi_monitor.format_status_message(rsi_status)}")
print(f"EMA: {ema_monitor.format_status_message(ema_status)}")
print(f"RSI-EMA: {rsi_ema_monitor.format_status_message(rsi_ema_status)}")
```

## 클래스별 상세 기능

### RSICalculator

#### 주요 메서드
- `calculate_rsi(data, column='close')`: RSI 시리즈 계산
- `check_buy_condition(data)`: 매수 조건 확인
- `check_sell_condition(data)`: 매도 조건 확인
- `analyze_rsi_trend(rsi_series)`: RSI 추세 분석

#### 반환 데이터 구조
```python
{
    'indicator': 'RSI',
    'current_value': 45.67,
    'slopes': {
        'slope_3': 2.34,
        'slope_5': 1.89
    },
    'analysis': {
        'buy_signal': True,
        'sell_signal': False,
        'all_slopes_positive': True,
        'rsi_overbought': False
    },
    'timestamp': '2024-01-01T12:00:00'
}
```

### EMACalculator

#### 주요 메서드
- `calculate_ema(data, column='close')`: EMA 시리즈 계산
- `check_buy_condition(data)`: 매수 조건 확인  
- `check_sell_condition(data)`: 매도 조건 확인
- `analyze_ema_trend(ema_series)`: EMA 추세 분석

#### 반환 데이터 구조
```python
{
    'indicator': 'EMA',
    'current_value': 1234.56,
    'slopes': {
        'slope_3': 0.35,
        'slope_5': 0.25
    },
    'analysis': {
        'buy_signal': True,
        'sell_signal': False,
        'threshold_checks': {
            'threshold_3': True,
            'threshold_5': True
        },
        'all_thresholds_met': True,
        'declining_trend': False
    },
    'timestamp': '2024-01-01T12:00:00'
}
```

### RSIEMACalculator

#### 주요 메서드
- `calculate_rsi_ema(data, column='close')`: RSI-EMA 시리즈 계산
- `check_buy_condition(data)`: 매수 조건 확인
- `check_sell_condition(data)`: 매도 조건 확인
- `get_detailed_analysis(data)`: 상세 분석 정보 제공

#### 반환 데이터 구조
```python
{
    'indicator': 'RSI_EMA',
    'current_value': 58.34,
    'slopes': {
        'slope_3': 0.45,
        'slope_5': 0.28
    },
    'analysis': {
        'buy_signal': True,
        'sell_signal': False,
        'threshold_checks': {
            'threshold_3': True,
            'threshold_5': True
        },
        'all_thresholds_met': True,
        'declining_trend': False
    },
    'timestamp': '2024-01-01T12:00:00'
}
```

#### 상세 분석 구조
```python
{
    'rsi_value': 64.78,
    'rsi_ema_value': 58.34,
    'rsi_ema_difference': 6.44,
    'slopes': {...},
    'threshold_checks': {...},
    'buy_signal': True,
    'sell_signal': False,
    'analysis_summary': {
        'rsi_above_ema': True,
        'momentum_strength': 'Strong',  # Strong/Moderate/Weak/Negative
        'trend_direction': 'Uptrend'    # Uptrend/Downtrend/Sideways
    },
    'timestamp': '2024-01-01T12:00:00'
}
```

### 모니터링 클래스

#### RSIMonitor
- `get_current_status(data)`: 현재 RSI 상태 조회
- `format_status_message(status)`: 상태 메시지 포맷팅

#### EMAMonitor  
- `get_current_status(data)`: 현재 EMA 상태 조회
- `format_status_message(status)`: 상태 메시지 포맷팅

#### RSIEMAMonitor
- `get_current_status(data)`: 현재 RSI-EMA 상태 조회
- `format_status_message(status)`: 상태 메시지 포맷팅

## 에러 처리

모든 함수는 예외 상황에서 안전하게 처리됩니다:

```python
buy_signal, analysis = get_rsi_buy_signal(data)

if 'error' in analysis:
    print(f"오류 발생: {analysis['error']}")
else:
    print(f"정상 처리: {analysis['current_value']}")
```

## 최소 데이터 요구사항

- **RSI(14)**: 최소 19개 봉 (14 + 5 for slope analysis)
- **EMA(20)**: 최소 25개 봉 (20 + 5 for slope analysis)
- **RSI-EMA**: 최소 39개 봉 (14 for RSI + 20 for EMA + 5 for slope analysis)

## 성능 최적화

- 벡터화된 pandas 연산 사용으로 빠른 계산 속도
- 메모리 효율적인 데이터 처리
- 불필요한 복사 최소화

## 예제 코드

완전한 사용 예제는 `simple_test.py` 파일을 참조하세요.

```bash
python simple_test.py
```