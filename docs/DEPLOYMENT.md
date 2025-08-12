# TEDER 코인원 자동매매 봇 배포 가이드

## 개요

이 문서는 TEDER 코인원 자동매매 봇을 Docker를 사용하여 24시간 안정적으로 운영하기 위한 배포 가이드입니다.

## 시스템 요구사항

### 최소 요구사항
- **CPU**: 2 Core 이상
- **메모리**: 2GB RAM 이상
- **디스크**: 20GB 이상 (로그 및 데이터 저장용)
- **네트워크**: 안정적인 인터넷 연결
- **OS**: Ubuntu 20.04 LTS 이상 권장

### 권장 요구사항
- **CPU**: 4 Core 이상
- **메모리**: 4GB RAM 이상
- **디스크**: 50GB 이상 (SSD 권장)
- **네트워크**: 전용 IP, 방화벽 설정

## 사전 준비

### 1. Docker 설치

```bash
# Ubuntu에서 Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER
newgrp docker
```

### 2. 코인원 API 키 발급

1. [코인원](https://coinone.co.kr)에 로그인
2. 마이페이지 → API 설정
3. API 키 생성 (거래 권한 포함)
4. Access Token과 Secret Key 기록

### 3. 서버 보안 설정

```bash
# 방화벽 설정
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 3000  # Grafana
sudo ufw allow 9090  # Prometheus
sudo ufw allow 8000  # 애플리케이션 모니터링

# 자동 업데이트 설정
sudo apt update
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

## 배포 절차

### 1. 소스 코드 다운로드

```bash
# 프로젝트 클론
git clone <repository-url> teder-trading-bot
cd teder-trading-bot

# 실행 권한 부여
chmod +x deploy/*.sh
chmod +x docker-entrypoint.sh
```

### 2. 환경 설정

```bash
# 환경 변수 파일 생성
cp .env.example .env

# 환경 변수 편집
nano .env
```

#### 필수 설정 항목

```bash
# 코인원 API 설정
COINONE_ACCESS_TOKEN=your_actual_access_token
COINONE_SECRET_KEY=your_actual_secret_key

# 거래 모드 (dry_run: 모의거래, live: 실거래)
TRADING_MODE=dry_run

# 보안 설정
GRAFANA_PASSWORD=your_secure_password
ENCRYPTION_KEY=your_32_byte_random_key

# 알림 설정 (선택사항)
SLACK_WEBHOOK_URL=your_slack_webhook
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. 초기 설정 실행

```bash
# 모든 초기 설정을 자동으로 실행
./deploy/deploy.sh setup

# 또는 단계별 실행
./deploy/monitoring-setup.sh
./deploy/logging-config.sh
```

### 4. 애플리케이션 빌드 및 시작

```bash
# Docker 이미지 빌드
./deploy/deploy.sh build

# 서비스 시작
./deploy/deploy.sh start

# 상태 확인
./deploy/deploy.sh status
```

## 운영 관리

### 일상 관리 명령어

```bash
# 서비스 상태 확인
./deploy/deploy.sh status

# 로그 확인
./deploy/deploy.sh logs
./deploy/deploy.sh logs -f  # 실시간 로그

# 서비스 재시작
./deploy/deploy.sh restart

# 서비스 중지
./deploy/deploy.sh stop

# 헬스체크
./deploy/deploy.sh health
```

### 데이터 백업 및 복원

```bash
# 데이터 백업
./deploy/deploy.sh backup

# 백업 파일 확인
ls -la backups/

# 데이터 복원
./deploy/deploy.sh restore backups/teder_backup_20240101_120000.tar.gz
```

### 애플리케이션 업데이트

```bash
# 최신 코드 업데이트 (자동 백업 포함)
./deploy/deploy.sh update

# 수동 업데이트
git pull origin main
./deploy/deploy.sh build
./deploy/deploy.sh restart
```

## 모니터링 대시보드

### 접속 정보

- **Grafana**: http://your-server:3000
  - 사용자: admin
  - 비밀번호: .env에서 설정한 GRAFANA_PASSWORD

- **Prometheus**: http://your-server:9090
  - 메트릭 수집 및 알림 규칙 관리

- **애플리케이션 상태**: http://your-server:8000
  - 실시간 거래 상태 모니터링

### 주요 모니터링 지표

1. **거래 지표**
   - 총 거래 횟수
   - 승률
   - 총 수익/손실
   - 현재 보유 자산

2. **시스템 지표**
   - CPU/메모리 사용률
   - 디스크 사용량
   - 네트워크 연결 상태
   - API 응답 시간

3. **알림 조건**
   - 애플리케이션 다운
   - 높은 에러율
   - 시스템 리소스 부족
   - API 연결 실패

## 보안 권장사항

### 1. 네트워크 보안

```bash
# 불필요한 포트 차단
sudo ufw deny <unnecessary_port>

# SSH 키 기반 인증 설정
ssh-keygen -t rsa -b 4096
# 공개키를 서버에 복사 후 비밀번호 인증 비활성화
```

### 2. 컨테이너 보안

```bash
# Docker 보안 스캔
docker scout cves teder/trading-bot:latest

# 컨테이너 권한 확인
docker exec teder-trading-bot whoami
docker exec teder-trading-bot id
```

### 3. 데이터 보안

```bash
# 환경 변수 파일 권한 설정
chmod 600 .env

# 백업 파일 암호화
gpg --symmetric --cipher-algo AES256 backup_file.tar.gz
```

## 로그 관리

### 로그 구조

```
logs/
├── teder.log              # 메인 애플리케이션 로그
├── trading/
│   └── trading.log        # 거래 실행 로그
├── system/
│   └── system.log         # 시스템 모니터링 로그
├── error/
│   └── error.log          # 에러 로그
└── archive/               # 압축된 과거 로그
```

### 로그 관리 명령어

```bash
# 로그 분석 리포트 생성
./deploy/analyze-logs.sh

# 로그 로테이션 실행
./deploy/rotate-logs.sh

# 로그 기반 알림 확인
./deploy/log-alert.sh
```

## 트러블슈팅

### 일반적인 문제

#### 1. 컨테이너가 시작되지 않는 경우

```bash
# 컨테이너 로그 확인
docker logs teder-trading-bot

# 환경 변수 확인
docker exec teder-trading-bot env | grep COINONE

# 헬스체크 실행
docker exec teder-trading-bot /app/healthcheck.sh
```

#### 2. API 연결 실패

```bash
# 네트워크 연결 테스트
curl -s https://api.coinone.co.kr/v2/ticker/?currency=usdt

# API 키 확인
# .env 파일의 COINONE_ACCESS_TOKEN, COINONE_SECRET_KEY 검증
```

#### 3. 디스크 공간 부족

```bash
# 디스크 사용량 확인
df -h

# 로그 정리
./deploy/deploy.sh clean

# 오래된 백업 삭제
find backups/ -name "*.tar.gz" -mtime +30 -delete
```

#### 4. 메모리 부족

```bash
# 메모리 사용량 확인
free -h
docker stats

# 컨테이너 리소스 제한 조정 (docker-compose.yml)
deploy:
  resources:
    limits:
      memory: 2G  # 메모리 제한 증가
```

### 응급 대응 절차

#### 1. 긴급 정지

```bash
# 안전한 거래 중지
echo "EMERGENCY_STOP=true" >> .env
./deploy/deploy.sh restart

# 또는 즉시 중지
./deploy/deploy.sh stop
```

#### 2. 데이터 복구

```bash
# 최신 백업에서 복구
./deploy/deploy.sh restore $(ls -t backups/*.tar.gz | head -1)

# 서비스 재시작
./deploy/deploy.sh start
```

## 성능 최적화

### 1. 시스템 최적화

```bash
# 스왑 설정 최적화
sudo sysctl vm.swappiness=10
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf

# 파일 디스크립터 한도 증가
echo 'ulimit -n 65536' >> ~/.bashrc
source ~/.bashrc
```

### 2. Docker 최적화

```bash
# Docker 로그 크기 제한
# docker-compose.yml에서 로그 설정 확인
logging:
  options:
    max-size: "10m"
    max-file: "3"
```

### 3. 애플리케이션 최적화

```bash
# Python 최적화 플래그 설정
export PYTHON_OPTIMIZE=1

# 가비지 컬렉션 튜닝
export GC_THRESHOLD1=700
export GC_THRESHOLD2=10
export GC_THRESHOLD3=10
```

## 자동화 설정

### 1. Systemd 서비스 등록

```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/teder-trading-bot.service
```

```ini
[Unit]
Description=TEDER Trading Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/teder-trading-bot
ExecStart=/path/to/teder-trading-bot/deploy/deploy.sh start
ExecStop=/path/to/teder-trading-bot/deploy/deploy.sh stop
TimeoutStartSec=0
User=ubuntu

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 등록 및 시작
sudo systemctl daemon-reload
sudo systemctl enable teder-trading-bot
sudo systemctl start teder-trading-bot
```

### 2. 크론 작업 설정

```bash
# 크론 작업 등록
crontab -e
```

```bash
# 매일 02:00에 백업
0 2 * * * /path/to/teder-trading-bot/deploy/deploy.sh backup

# 매주 일요일 03:00에 로그 정리
0 3 * * 0 /path/to/teder-trading-bot/deploy/deploy.sh clean

# 매시간 헬스체크
0 * * * * /path/to/teder-trading-bot/deploy/deploy.sh health
```

## 고가용성 설정

### 1. 다중 인스턴스 구성

```bash
# docker-compose.override.yml 생성
cat > docker-compose.override.yml << 'EOF'
version: '3.8'
services:
  teder-trading-bot:
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
EOF
```

### 2. 외부 데이터베이스 연결

```bash
# Redis 클러스터 연결 설정
REDIS_HOST=redis-cluster.example.com
REDIS_PORT=6379
REDIS_PASSWORD=secure_password
```

## 지원 및 문의

### 로그 수집

문제 발생 시 다음 정보를 수집하여 제공해주세요:

```bash
# 시스템 정보 수집
./deploy/collect-debug-info.sh
```

### 문의처

- **이슈 리포트**: GitHub Issues
- **긴급 문의**: support@teder-bot.com
- **문서**: https://docs.teder-bot.com

---

## 면책 조항

⚠️ **중요 공지**

1. 이 소프트웨어는 교육 및 연구 목적으로 제공됩니다.
2. 실제 거래에 사용할 경우 모든 위험은 사용자가 부담합니다.
3. 암호화폐 거래는 높은 위험을 수반하며 원금 손실 가능성이 있습니다.
4. 충분한 테스트 없이 실거래에 사용하지 마세요.
5. 정기적인 모니터링과 관리가 필요합니다.

---

© 2024 TEDER Trading Bot. All rights reserved.