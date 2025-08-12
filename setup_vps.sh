#!/bin/bash
# VPS 서버 설정 스크립트 (Ubuntu/Debian 기준)

echo "=========================================="
echo "USDT/KRW 자동매매 VPS 설정"
echo "=========================================="
echo ""

# 시스템 업데이트
echo "시스템 패키지 업데이트 중..."
sudo apt-get update
sudo apt-get upgrade -y

# Python 3.8+ 설치
echo "Python 설치 중..."
sudo apt-get install -y python3 python3-pip python3-venv

# Git 설치
echo "Git 설치 중..."
sudo apt-get install -y git

# 프로젝트 클론
echo "프로젝트 클론 중..."
cd /home/$USER
git clone https://github.com/your-username/teder-trading-bot.git
cd teder-trading-bot

# 가상환경 생성
echo "가상환경 생성 중..."
python3 -m venv venv
source venv/bin/activate

# 필요한 패키지 설치
echo "Python 패키지 설치 중..."
pip install -r requirements.txt

# .env 파일 생성
echo "환경 설정 파일 생성..."
cp .env.example .env
echo ""
echo "!!! 중요 !!!"
echo ".env 파일을 편집하여 API 키를 입력하세요:"
echo "nano .env"
echo ""

# systemd 서비스 파일 생성
echo "시스템 서비스 생성 중..."
sudo tee /etc/systemd/system/trading-bot.service > /dev/null <<EOF
[Unit]
Description=USDT/KRW Trading Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/teder-trading-bot
Environment="PATH=/home/$USER/teder-trading-bot/venv/bin"
ExecStart=/home/$USER/teder-trading-bot/venv/bin/python /home/$USER/teder-trading-bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 서비스 권한 설정
sudo chmod 644 /etc/systemd/system/trading-bot.service

# 로그 디렉토리 생성
mkdir -p logs

echo ""
echo "=========================================="
echo "설정 완료!"
echo ""
echo "다음 단계:"
echo "1. API 키 설정: nano .env"
echo "2. 서비스 시작: sudo systemctl start trading-bot"
echo "3. 서비스 활성화: sudo systemctl enable trading-bot"
echo "4. 로그 확인: sudo journalctl -u trading-bot -f"
echo "=========================================="