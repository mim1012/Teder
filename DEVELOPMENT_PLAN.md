# 코인원 USDT/KRW 자동매매 봇 개발 계획

## 1. 프로젝트 아키텍처

### 1.1 시스템 구성도
```
┌─────────────────────────────────────────────────────────┐
│                   Main Controller                        │
│  - 전략 실행 관리                                        │
│  - 상태 관리 (매수대기/보유중/매도대기)                 │
│  - 무한루프 및 재시작 타이머                           │
└─────────────────┬───────────────────────────────────────┘
                  │
    ┌─────────────┴─────────────┬────────────────┬────────────────┐
    │                           │                │                │
┌───▼────────────┐  ┌──────────▼─────────┐  ┌──▼──────────┐  ┌──▼──────────┐
│ Coinone API    │  │ Technical          │  │ Trading     │  │ Monitor     │
│ Module         │  │ Indicators Module  │  │ Strategy    │  │ & Logger    │
├────────────────┤  ├────────────────────┤  ├─────────────┤  ├─────────────┤
│- 시세조회      │  │- RSI 계산          │  │- 매수판단   │  │- 실시간화면 │
│- 호가조회      │  │- EMA 계산          │  │- 매도판단   │  │- 로그기록   │
│- 주문실행      │  │- 기울기 계산       │  │- 주문관리   │  │- 수익률계산 │
│- 잔고조회      │  │- 1시간봉 데이터    │  │- 포지션관리 │  │- 에러알림   │
└────────────────┘  └────────────────────┘  └─────────────┘  └─────────────┘
```

### 1.2 프로젝트 디렉토리 구조
```
coinone-trading-bot/
├── config/
│   ├── __init__.py
│   ├── settings.py      # API 키, 거래 설정
│   └── constants.py     # 상수 정의
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── coinone_client.py  # 코인원 API 클라이언트
│   │   └── auth.py            # API 인증
│   ├── indicators/
│   │   ├── __init__.py
│   │   ├── rsi.py            # RSI 계산
│   │   └── ema.py            # EMA 계산
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── trading_strategy.py  # 매매 전략
│   │   └── position_manager.py  # 포지션 관리
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py         # 로깅
│   │   └── helpers.py        # 유틸리티 함수
│   └── ui/
│       ├── __init__.py
│       └── monitor.py        # 실시간 모니터링
├── tests/
│   ├── __init__.py
│   ├── test_indicators.py
│   ├── test_strategy.py
│   └── test_backtest.py
├── backtest/
│   ├── __init__.py
│   ├── backtest_engine.py   # 백테스트 엔진
│   └── data_loader.py       # 과거 데이터 로더
├── main.py                  # 메인 실행 파일
├── requirements.txt         # 의존성 패키지
├── Dockerfile              # Docker 설정
├── docker-compose.yml      # Docker Compose 설정
└── README.md              # 프로젝트 문서

```

## 2. 핵심 모듈 설계

### 2.1 Coinone API Client
- Public API: 시세조회, 호가조회, 1시간봉 데이터
- Private API: 잔고조회, 주문실행, 주문취소, 거래내역
- WebSocket: 실시간 가격 업데이트 (선택사항)

### 2.2 Technical Indicators
- RSI(14) 계산 및 기울기 분석
- EMA(20) 계산 및 기울기 분석
- 1시간봉 데이터 관리 및 업데이트

### 2.3 Trading Strategy
- 매수 조건 검증 로직
- 매도 조건 검증 로직
- 주문 관리 (부분체결, 미체결 처리)
- 포지션 상태 관리

### 2.4 Monitoring System
- 실시간 정보 표시 (curses 또는 rich 라이브러리 사용)
- 로그 파일 저장
- 에러 알림 시스템

## 3. 개발 단계별 계획

### Phase 1: 기초 구조 설정 (1-2일)
1. 프로젝트 디렉토리 구조 생성
2. 필요 라이브러리 설치 및 환경 설정
3. 설정 파일 및 상수 정의
4. 기본 로깅 시스템 구축

### Phase 2: API 연동 모듈 개발 (2-3일)
1. Coinone API 클라이언트 구현
2. 인증 시스템 구현
3. 주요 API 메서드 구현 및 테스트
4. 에러 처리 및 재시도 로직

### Phase 3: 기술적 지표 모듈 개발 (2일)
1. RSI 계산 로직 구현
2. EMA 계산 로직 구현
3. 기울기 계산 함수 구현
4. 지표 검증 테스트

### Phase 4: 매매 전략 구현 (3-4일)
1. 매수 조건 판단 로직
2. 매도 조건 판단 로직
3. 주문 실행 및 관리
4. 포지션 상태 관리

### Phase 5: 백테스트 시스템 (2-3일)
1. 과거 데이터 수집
2. 백테스트 엔진 구현
3. 전략 성과 분석
4. 최적화 및 개선

### Phase 6: 모니터링 및 배포 (2일)
1. 실시간 모니터링 UI 개발
2. Docker 컨테이너화
3. 가상서버 배포 설정
4. 운영 매뉴얼 작성

## 4. 주요 기술 스택

### Backend
- Python 3.9+
- pandas: 데이터 처리
- numpy: 수치 계산
- requests: HTTP 통신
- websocket-client: 실시간 데이터 (선택)
- ta-lib 또는 pandas-ta: 기술적 지표 계산

### UI/Monitoring
- rich 또는 curses: 터미널 UI
- logging: 로그 관리
- matplotlib: 차트 시각화 (백테스트)

### Deployment
- Docker & Docker Compose
- Ubuntu Server (가상서버)
- systemd: 서비스 관리
- nginx: 리버스 프록시 (선택)

## 5. 리스크 관리 및 안전장치

1. **API 제한사항 준수**
   - Rate Limit 관리
   - 요청 간격 조절

2. **에러 처리**
   - 네트워크 오류 재시도
   - API 오류 로깅
   - 예외 상황 알림

3. **거래 안전장치**
   - 최대 주문 금액 제한
   - 일일 거래 횟수 제한
   - 긴급 정지 기능

4. **데이터 백업**
   - 거래 내역 저장
   - 포지션 상태 저장
   - 로그 파일 백업

## 6. 예상 일정

총 개발 기간: 약 2-3주
- 개발: 12-15일
- 테스트 및 디버깅: 3-5일
- 배포 및 안정화: 2-3일

## 7. 백테스트 계획

1. 과거 3-6개월 USDT/KRW 1시간봉 데이터 수집
2. 다양한 시장 상황에서 전략 테스트
3. 수익률, 승률, MDD 등 성과 지표 분석
4. 파라미터 최적화 (필요시)
5. 실제 거래 전 Paper Trading 진행