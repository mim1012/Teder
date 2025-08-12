# VPS 서버 24시간 실거래 봇 구축 가이드

## 1. VPS 서버 선택 및 구매

### 권장 VPS 제공업체
- **Vultr**: 시간당 과금, 한국/일본 리전 제공
- **DigitalOcean**: 안정적, 문서 풍부
- **Linode**: 가성비 좋음
- **AWS EC2**: t3.micro 프리티어 가능

### 최소 사양
- CPU: 1 vCore
- RAM: 2GB
- Storage: 20GB SSD
- OS: Ubuntu 22.04 LTS
- 지역: 한국/일본 (낮은 지연시간)
- 가격: 월 $5-10

## 2. 서버 초기 설정

### 2.1 서버 접속
```bash
# Windows PowerShell 또는 PuTTY 사용
ssh root@서버IP
```

### 2.2 기본 보안 설정
```bash
# 시스템 업데이트
apt update && apt upgrade -y

# 새 사용자 생성
adduser teder
usermod -aG sudo teder

# SSH 키 설정
su - teder
mkdir ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
# 본인의 SSH 공개키 붙여넣기
chmod 600 ~/.ssh/authorized_keys

# SSH 설정 변경
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no
# PasswordAuthentication no
sudo systemctl restart ssh
```

## 3. 프로젝트 업로드 및 설정

### 3.1 Git으로 코드 업로드
```bash
# Git 설치
sudo apt install git -y

# 프로젝트 클론
cd ~
git clone https://github.com/당신의저장소/Teder.git
cd Teder
```

### 3.2 직접 업로드 (대안)
```bash
# 로컬 PC에서 (PowerShell)
scp -r D:\Project\Teder teder@서버IP:~/
```

### 3.3 환경 변수 설정
```bash
# .env 파일 생성
cp .env.example .env
nano .env

# 아래 내용 수정
COINONE_ACCESS_TOKEN=당신의_액세스_토큰
COINONE_SECRET_KEY=당신의_시크릿_키
DRY_RUN=false  # 실거래 모드
TICKER=USDT
CURRENCY=KRW
```

## 4. Docker 설치 및 배포

### 4.1 Docker 설치
```bash
# Docker 설치 스크립트 실행
chmod +x deploy.sh
./deploy.sh setup
```

### 4.2 봇 배포
```bash
# Docker 이미지 빌드 및 실행
./deploy.sh deploy

# 상태 확인
./deploy.sh status

# 로그 확인
./deploy.sh logs --follow
```

## 5. 24시간 자동 운영 설정

### 5.1 Systemd 서비스 등록
```bash
# 서비스 파일 복사
sudo cp systemd/teder-bot.service /etc/systemd/system/

# 서비스 활성화
sudo systemctl enable teder-bot
sudo systemctl start teder-bot

# 상태 확인
sudo systemctl status teder-bot
```

### 5.2 자동 재시작 설정
```bash
# Docker 컨테이너 자동 재시작 확인
docker update --restart unless-stopped teder-bot
```

## 6. 모니터링 설정

### 6.1 실시간 모니터링
```bash
# 로그 실시간 확인
docker logs -f teder-bot

# 시스템 리소스 확인
docker stats teder-bot

# 거래 로그 확인
tail -f logs/trading_*.log
```

### 6.2 원격 모니터링 (선택사항)
```bash
# Telegram 알림 설정 (.env 파일)
TELEGRAM_BOT_TOKEN=봇토큰
TELEGRAM_CHAT_ID=채팅ID
```

## 7. 보안 강화

### 7.1 방화벽 설정
```bash
# UFW 방화벽 설정
sudo ufw allow 22/tcp  # SSH
sudo ufw --force enable
```

### 7.2 Fail2Ban 설정
```bash
# Fail2Ban 설치
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
```

## 8. 유지보수

### 8.1 일일 점검
```bash
# 봇 상태 확인
./deploy.sh status

# 로그 확인
./deploy.sh logs --tail 100

# 리소스 사용량 확인
docker stats --no-stream
```

### 8.2 업데이트
```bash
# 코드 업데이트
git pull origin main

# 재배포
./deploy.sh update
```

### 8.3 백업
```bash
# 로그 백업
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/

# 데이터베이스 백업 (있는 경우)
./deploy.sh backup
```

## 9. 문제 해결

### 봇이 중지된 경우
```bash
# 컨테이너 재시작
docker restart teder-bot

# 서비스 재시작
sudo systemctl restart teder-bot
```

### API 오류 발생시
```bash
# 환경 변수 확인
docker exec teder-bot printenv | grep COINONE

# API 키 재설정
nano .env
./deploy.sh update
```

### 메모리 부족시
```bash
# 스왑 파일 생성
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 10. 비용 관리

### 예상 월 비용
- VPS 서버: $5-10
- 네트워크: 포함
- 백업 스토리지: $1-2 (선택)
- **총: 약 $6-12/월**

### 비용 절감 팁
1. 작은 인스턴스로 시작
2. 예약 인스턴스 사용 (AWS/Azure)
3. 불필요한 로그 정리
4. 자동 스케일링 비활성화

## 중요 체크리스트

### 배포 전
- [ ] API 키 설정 확인
- [ ] DRY_RUN=false 설정
- [ ] 충분한 잔고 확인
- [ ] 백테스트 완료

### 배포 후
- [ ] 봇 실행 상태 확인
- [ ] 첫 거래 모니터링
- [ ] 로그 정상 생성 확인
- [ ] 자동 재시작 테스트

## 연락처 및 지원

문제 발생시:
1. 로그 파일 확인
2. Docker 상태 확인
3. 시스템 리소스 확인
4. API 연결 상태 확인

---

**경고**: 실거래 모드는 실제 자금을 사용합니다. 
충분한 테스트 후 신중하게 운영하세요.