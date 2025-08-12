# 코인원 USDT/KRW 자동매매 봇

RSI와 EMA 지표를 활용한 코인원 거래소 USDT/KRW 자동매매 프로그램입니다.

## 주요 기능

- RSI(14)와 EMA(20) 기술적 지표 기반 매매
- 자동 익절/손절 시스템
- 실시간 모니터링 대시보드
- 백테스트 지원
- Docker 기반 24시간 운영

## 설치 방법

### 1. 프로젝트 클론
```bash
git clone https://github.com/yourusername/coinone-trading-bot.git
cd coinone-trading-bot
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. 의존성 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 열어 API 키 입력
```

## 사용 방법

### 모의거래 모드 (기본값)
```bash
python main.py
```

### 실거래 모드
```bash
python main.py --live
```

### 백테스트 실행
```bash
python main.py --backtest
```

### 디버그 모드
```bash
python main.py --debug
```

## 프로젝트 구조

```
coinone-trading-bot/
├── config/             # 설정 파일
├── src/
│   ├── api/           # 코인원 API 클라이언트
│   ├── indicators/    # 기술적 지표 계산
│   ├── strategy/      # 매매 전략 구현
│   ├── utils/         # 유틸리티 함수
│   └── ui/           # 모니터링 UI
├── tests/            # 테스트 코드
├── backtest/         # 백테스트 엔진
├── logs/             # 로그 파일
└── main.py          # 메인 실행 파일
```

## 매매 전략

### 매수 조건
- RSI(14) 직전 3봉, 5봉 기울기 > 0
- EMA(20) 직전 3봉 기울기 >= 0.3
- EMA(20) 직전 5봉 기울기 >= 0.2

### 매도 조건
- 익절: 평균매수가 + 4원
- 손절: 24시간 경과, RSI > 70, EMA 기울기 감소

## 주의사항

- 실거래 전 반드시 충분한 백테스트를 수행하세요
- API 키는 절대 공개하지 마세요
- 투자에 대한 책임은 사용자 본인에게 있습니다

## 라이센스

MIT License