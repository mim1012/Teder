# USDT/KRW 자동매매 프로그램 실행 가이드

## 1. 테스트 환경 실행 (Paper Trading)

### 초기 설정
1. `.env` 파일 확인:
   ```
   COINONE_ACCESS_TOKEN=your_access_token
   COINONE_SECRET_KEY=your_secret_key
   DRY_RUN=True  # 모의거래 모드
   ```

2. 테스트 실행:
   ```
   run_test_en.bat     # 간단한 테스트 버전
   run_live_final.bat  # 전체 기능 버전 (DRY_RUN=True)
   ```

### 테스트 체크리스트
- [ ] API 연결 확인 (잔고 조회)
- [ ] 캔들 데이터 수신 확인
- [ ] RSI/EMA 지표 계산 확인
- [ ] 매수 신호 감지 확인
- [ ] 매도 신호 감지 확인
- [ ] 로그 파일 생성 확인 (logs/live_trading.log)

## 2. 실전 거래 전환 (Live Trading)

### 주의사항
**경고: 실전 거래는 실제 자금을 사용합니다!**
- 소액으로 시작하여 시스템 안정성 확인
- 최소 100,000 KRW 이상 입금 필요
- 24시간 모니터링 권장

### 실전 거래 활성화
1. `.env` 파일 수정:
   ```
   DRY_RUN=False  # 실거래 모드 활성화
   ```

2. 실행:
   ```
   run_live_final.bat
   ```

3. 10초 카운트다운 후 자동 시작

## 3. 프로그램 구조

### 메인 파일들
- **main_live.py**: 실전/모의거래 통합 버전
  - 완전한 주문 관리 시스템
  - 부분체결 처리 (10분 타임아웃)
  - 실시간 포지션 추적
  
- **main_simple.py**: 간단한 테스트 버전
  - 기본 로직 검증용
  - 시뮬레이션 데이터 사용

- **main.py**: 원본 버전 (복잡한 구조)

### 실행 파일들
- **run_live_final.bat**: 실전 거래용
- **run_test_en.bat**: 테스트용

## 4. 매매 전략 요약

### 매수 조건 (AND)
- RSI(14) 3봉 기울기 > 0
- RSI(14) 5봉 기울기 > 0
- EMA(20) 3봉 기울기 >= 0.3
- EMA(20) 5봉 기울기 >= 0.2

### 매도 조건 (OR)
1. **익절**: 평균매수가 + 4 KRW
2. **타임아웃**: 24시간 경과
3. **RSI 과매수**: RSI > 70
4. **EMA 하락**: 3봉 기울기 지속 감소

## 5. 모니터링

### 로그 확인
```
tail -f logs/live_trading.log
```

### 주요 로그 메시지
- `BUY SIGNAL DETECTED`: 매수 신호 감지
- `[LIVE] Buy order placed`: 실제 매수 주문
- `SELL ORDER`: 매도 주문
- `PnL`: 손익 정보

## 6. 문제 해결

### API 오류
- 인증 실패: API 키 확인
- 잔고 부족: 최소 100,000 KRW 필요
- 주문 실패: 최소 주문 금액 10,000 KRW

### 프로그램 중단
- Ctrl+C로 안전하게 종료
- 포지션 있을 경우 경고 메시지 표시
- 수동으로 포지션 정리 필요할 수 있음

## 7. 안전 장치

### 자동 안전 기능
- 최소 주문 금액 체크 (10,000 KRW)
- 수수료 여유분 확보 (0.1%)
- 소수점 4자리 반올림
- 10분 미체결 주문 자동 취소

### 수동 확인 사항
- 24시간 운영 가능한 환경
- 안정적인 인터넷 연결
- 정기적인 로그 확인
- 이상 징후 시 즉시 중단

## 8. 배포 (VPS)

### Docker 설정 (추후 구현)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main_live.py"]
```

### 자동 재시작 설정
```bash
# systemd service 파일 생성
sudo nano /etc/systemd/system/coinone-bot.service

[Unit]
Description=Coinone Trading Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/teder
ExecStart=/usr/bin/python3 /home/ubuntu/teder/main_live.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 9. 성능 지표

### 백테스트 결과
- 기간: 최근 30일
- 초기 자금: 100,000 KRW
- 예상 수익률: 변동적 (시장 상황 의존)

### 실전 거래 목표
- 일 평균 거래: 1-3회
- 목표 수익: 회당 +4 KRW
- 최대 손실: -24시간 보유 후 청산

## 10. 연락처

문제 발생 시:
1. 즉시 프로그램 중단 (Ctrl+C)
2. 로그 파일 확인
3. 코인원 계정에서 포지션 확인
4. 필요시 수동 청산

---

**마지막 업데이트**: 2025-08-06
**버전**: 1.0.0 (Live Trading Ready)