# API 키 설정 가이드

## 1. 코인원 API 키 발급

### 1.1 코인원 웹사이트 접속
1. [https://coinone.co.kr](https://coinone.co.kr) 로그인
2. 우측 상단 프로필 → 계정 설정

### 1.2 API 관리
1. 좌측 메뉴에서 "API 관리" 클릭
2. "새 API 키 생성" 버튼 클릭

### 1.3 API 권한 설정
필수 권한:
- [x] 잔고 조회
- [x] 주문 조회
- [x] 주문 생성
- [x] 주문 취소

선택 권한:
- [ ] 출금 (보안상 권장하지 않음)

### 1.4 보안 설정
1. **IP 화이트리스트**: VPS 서버 IP 주소 입력 (권장)
2. **API 키 이름**: 식별 가능한 이름 입력 (예: "USDT자동매매")

### 1.5 API 키 저장
1. **Access Token**: 긴 문자열 (예: c3d4cd31-8c4e-4c6f-a645-8c2c28b4deed)
2. **Secret Key**: Base64 인코딩된 문자열

⚠️ **중요**: Secret Key는 생성 시에만 확인 가능하므로 안전한 곳에 저장하세요!

## 2. .env 파일 설정

### 2.1 파일 복사
```batch
copy .env.example .env
```

### 2.2 .env 파일 편집
메모장으로 .env 파일을 열어 편집:
```batch
notepad .env
```

### 2.3 API 키 입력
```env
# 코인원 API 설정
COINONE_ACCESS_TOKEN=c3d4cd31-8c4e-4c6f-a645-8c2c28b4deed
COINONE_SECRET_KEY=MEIWbmF1Z2h0eSBib3kgb3UncmU=

# 거래 모드 설정
DRY_RUN=True  # 처음에는 True로 테스트

# 로그 레벨
DEBUG=False

# 기타 설정
TIMEZONE=Asia/Seoul
```

## 3. API 키 테스트

### 3.1 잔고 확인
```batch
check_balance.bat
```

정상 출력 예시:
```
계좌 잔고:
----------------------------------------
KRW (원화):
  사용가능: 1,000,000원
  거래중: 0원
  총액: 1,000,000원

USDT (테더):
  사용가능: 0.0000개
  거래중: 0.0000개
  총액: 0.0000개
```

### 3.2 시세 확인
```batch
check_market.bat
```

## 4. 보안 주의사항

### 4.1 파일 보안
- `.env` 파일은 절대 Git에 커밋하지 마세요
- `.gitignore`에 `.env`가 포함되어 있는지 확인

### 4.2 API 키 보안
- API 키는 타인과 공유하지 마세요
- 출금 권한은 부여하지 마세요
- IP 화이트리스트를 설정하세요

### 4.3 정기적인 관리
- 3개월마다 API 키 재발급 권장
- 사용하지 않는 API 키는 삭제
- 의심스러운 활동 발견 시 즉시 키 폐기

## 5. 문제 해결

### 5.1 "Invalid API Key" 오류
- Access Token과 Secret Key가 정확히 입력되었는지 확인
- 복사 시 앞뒤 공백이 포함되지 않았는지 확인

### 5.2 "Insufficient Permission" 오류
- API 권한 설정에서 필요한 권한이 모두 체크되었는지 확인
- 코인원 웹사이트에서 API 권한 재설정

### 5.3 "Invalid Signature" 오류
- Secret Key가 올바르게 입력되었는지 확인
- Base64 인코딩이 깨지지 않았는지 확인

## 6. 실거래 전 체크리스트

- [ ] API 키 발급 완료
- [ ] .env 파일에 API 키 입력
- [ ] check_balance.bat으로 잔고 확인
- [ ] check_market.bat으로 시세 확인
- [ ] run_test.bat으로 모의거래 테스트
- [ ] 소액으로 실거래 테스트
- [ ] VPS 서버 준비
- [ ] IP 화이트리스트 설정