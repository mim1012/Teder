# 실시간 모니터링 UI 사용 가이드

Rich 라이브러리 기반의 터미널 UI로 코인원 USDT/KRW 자동매매 시스템을 실시간 모니터링할 수 있습니다.

## 주요 기능

### 화면 구성
- **상단**: 현재가, 변동률, 보유 USDT/KRW, 평균매수가, 수익률
- **중앙**: 매수/매도 신호, 주문 상태, RSI/EMA 지표값  
- **하단**: 거래 로그, 시스템 로그

### 실시간 업데이트
- 1초마다 자동 화면 갱신
- 비동기 처리로 블로킹 없는 실시간 모니터링
- 색상 구분으로 직관적인 정보 표시

### 색상 스키마
- 🟢 **수익**: 녹색
- 🔴 **손실**: 빨간색  
- 🔵 **매수 신호**: 파란색
- 🟡 **매도 신호**: 노란색
- ⚪ **중립**: 흰색

## 사용 방법

### 1. 전체 시스템 실행 (실제 거래)
```bash
python run_trading_with_monitor.py
```

### 2. 모니터링 UI만 테스트
```bash
python run_trading_with_monitor.py monitor-only
```

### 3. 개별 컴포넌트 테스트
```bash
python test_monitor_ui.py components
```

### 4. 모의 데이터로 UI 테스트
```bash
python test_monitor_ui.py
```

## 모니터링 정보

### 시장 정보 패널
- **Current Price**: 현재 USDT/KRW 가격
- **Change**: 가격 변동량 및 변동률
- **Volume**: 24시간 거래량
- **Last Update**: 마지막 업데이트 시간

### 잔고 정보 패널
- **KRW**: 보유 원화
- **USDT**: 보유 테더
- **Total**: 총 자산 가치 (KRW 기준)

### 포지션 정보 패널
- **Avg Buy Price**: 평균 매수가
- **Quantity**: 보유 수량
- **Current Price**: 현재가
- **Profit Target**: 익절 목표가 (평균매수가 + 4원)
- **Unrealized P&L**: 미실현 수익/손실

### 신호 정보 패널
- **RSI(14)**: RSI 지표값과 매수 신호 상태
- **EMA(20)**: EMA 지표값과 매수 신호 상태
- **EMA Slope**: 3봉/5봉 기울기 조건 충족 여부

### 주문 정보 패널
- 활성 주문들의 상태 (FILLED/PENDING/CANCELLED)
- 주문 시간, 타입, 매수/매도, 수량, 가격

### 거래 로그 패널
- 매수/매도 체결 내역
- 수익 실현/손절 기록
- 각 거래의 손익 정보

### 시스템 로그 패널
- 시스템 동작 상태
- 에러 및 경고 메시지
- API 연결 상태

## 단축키

- **Ctrl+C**: 시스템 종료
- **q**: 모니터링 종료 (일부 모드에서)

## 설정

### MonitoringConfig 옵션
```python
config = MonitoringConfig(
    refresh_rate=1.0,           # 화면 갱신 주기 (초)
    max_log_entries=100,        # 최대 시스템 로그 수
    max_trade_logs=50,          # 최대 거래 로그 수
    console_width=None,         # 콘솔 너비 (자동)
    console_height=None,        # 콘솔 높이 (자동)
    debug_mode=False            # 디버그 모드
)
```

## 프로그래밍 인터페이스

### 기본 사용법
```python
from src.ui.monitor import TradingMonitor, MonitoringConfig

# 모니터 생성
monitor = TradingMonitor(MonitoringConfig(refresh_rate=1.0))

# 데이터 콜백 설정
monitor.set_data_callback(your_strategy.execute_cycle)

# 모니터링 시작
monitor.start_monitoring()
```

### 로깅 기능
```python
# 시스템 이벤트 로깅
monitor.log_system_event("INFO", "System initialized")
monitor.log_system_event("ERROR", "Connection failed")

# 거래 이벤트 로깅
monitor.log_trade_event("buy_order_filled", "Buy order executed", pnl=0, quantity=1.0, price=1250)

# 알림 추가
monitor.add_alert("Trading started", "success")
monitor.add_alert("High volatility detected", "warning")
```

### 비동기 모니터링
```python
# 백그라운드에서 모니터링 실행
monitor.start_monitoring_async()

# 메인 스레드에서 다른 작업 수행
while True:
    # 거래 로직 실행
    result = strategy.execute_cycle()
    monitor.update_strategy_result(result)
    time.sleep(60)
```

## 주의사항

1. **터미널 크기**: 최소 80x24 크기의 터미널 권장
2. **색상 지원**: ANSI 색상을 지원하는 터미널에서 최적 표시
3. **성능**: 1초 갱신 주기로 CPU 사용률이 약간 증가할 수 있음
4. **메모리**: 로그 데이터가 메모리에 누적되므로 장기 실행 시 주의

## 문제 해결

### 화면이 깨져 보이는 경우
- 터미널 크기를 늘려보세요
- ANSI 색상을 지원하는 터미널을 사용하세요

### 업데이트가 느린 경우
- `refresh_rate` 값을 늘려보세요 (예: 2.0)
- 네트워크 연결 상태를 확인하세요

### 메모리 사용량이 높은 경우
- `max_log_entries`와 `max_trade_logs` 값을 줄여보세요
- 주기적으로 시스템을 재시작하세요

## 개발자 정보

### 파일 구조
```
src/ui/
├── __init__.py          # 모듈 초기화
├── components.py        # UI 컴포넌트
├── dashboard.py         # 대시보드 레이아웃
└── monitor.py          # 메인 모니터링 클래스
```

### 확장 가능성
- 새로운 UI 컴포넌트 추가
- 차트 표시 기능 구현
- 웹 대시보드 연동
- 알림 시스템 확장 (이메일, 슬랙 등)

## 라이센스

이 모니터링 UI는 메인 프로젝트와 동일한 라이센스를 따릅니다.