#!/bin/bash
# =============================================================================
# TEDER Trading Bot 디버그 정보 수집 스크립트
# =============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DEBUG_DIR="$PROJECT_DIR/debug-info"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEBUG_FILE="$DEBUG_DIR/debug-info-$TIMESTAMP.txt"

# 로그 함수
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 디버그 디렉토리 생성
mkdir -p "$DEBUG_DIR"

# 디버그 정보 수집 시작
{
    echo "==================================================================="
    echo "TEDER Trading Bot 디버그 정보"
    echo "생성 시간: $(date)"
    echo "==================================================================="
    echo ""

    # 시스템 정보
    echo "=== 시스템 정보 ==="
    echo "OS: $(uname -a)"
    echo "커널: $(uname -r)"
    echo "배포판: $(lsb_release -d 2>/dev/null || echo 'Unknown')"
    echo "업타임: $(uptime)"
    echo ""

    # CPU 정보
    echo "=== CPU 정보 ==="
    echo "CPU 모델: $(lscpu | grep 'Model name' | cut -d':' -f2 | xargs)"
    echo "CPU 코어: $(nproc)"
    echo "CPU 사용률:"
    top -bn1 | grep "Cpu(s)" | head -3
    echo ""

    # 메모리 정보
    echo "=== 메모리 정보 ==="
    free -h
    echo ""
    echo "메모리 상세:"
    cat /proc/meminfo | head -10
    echo ""

    # 디스크 정보
    echo "=== 디스크 정보 ==="
    df -h
    echo ""
    echo "inode 사용량:"
    df -i
    echo ""

    # 네트워크 정보
    echo "=== 네트워크 정보 ==="
    echo "네트워크 인터페이스:"
    ip addr show
    echo ""
    echo "라우팅 테이블:"
    ip route show
    echo ""
    echo "DNS 설정:"
    cat /etc/resolv.conf
    echo ""

    # Docker 정보
    echo "=== Docker 정보 ==="
    echo "Docker 버전:"
    docker --version
    docker-compose --version
    echo ""
    echo "Docker 상태:"
    systemctl status docker --no-pager -l
    echo ""
    echo "Docker 이미지:"
    docker images | grep -E "(teder|trading)"
    echo ""
    echo "실행 중인 컨테이너:"
    docker ps -a --filter name=teder
    echo ""

    # 컨테이너 상세 정보
    echo "=== 컨테이너 상세 정보 ==="
    if docker ps -q --filter name=teder-trading-bot >/dev/null 2>&1; then
        echo "컨테이너 상태:"
        docker inspect teder-trading-bot --format='{{json .State}}' | jq '.' 2>/dev/null || cat
        echo ""
        echo "컨테이너 리소스 사용량:"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" | grep teder
        echo ""
    else
        echo "teder-trading-bot 컨테이너가 실행되지 않고 있습니다."
        echo ""
    fi

    # Docker Compose 서비스 상태
    echo "=== Docker Compose 서비스 ==="
    cd "$PROJECT_DIR"
    docker-compose ps
    echo ""
    docker-compose config --services
    echo ""

    # 환경 변수 (민감한 정보 제외)
    echo "=== 환경 변수 (마스킹됨) ==="
    if [ -f "$PROJECT_DIR/.env" ]; then
        grep -v -E "(TOKEN|KEY|PASSWORD|SECRET)" "$PROJECT_DIR/.env" | head -20
        echo "... (민감한 정보는 마스킹되었습니다)"
    else
        echo ".env 파일이 없습니다."
    fi
    echo ""

    # 프로젝트 구조
    echo "=== 프로젝트 구조 ==="
    find "$PROJECT_DIR" -type f -name "*.py" -o -name "*.yml" -o -name "*.sh" | head -20
    echo "... (일부만 표시)"
    echo ""

    # 최근 로그 (에러 및 중요 이벤트)
    echo "=== 최근 로그 (에러 및 경고) ==="
    if [ -f "$PROJECT_DIR/logs/teder.log" ]; then
        echo "메인 로그 (최근 50줄):"
        tail -50 "$PROJECT_DIR/logs/teder.log" | grep -E "(ERROR|CRITICAL|WARNING)" | tail -10
        echo ""
    fi

    if [ -f "$PROJECT_DIR/logs/error.log" ]; then
        echo "에러 로그 (최근 20줄):"
        tail -20 "$PROJECT_DIR/logs/error.log"
        echo ""
    fi

    # Docker 로그
    echo "=== Docker 컨테이너 로그 ==="
    if docker ps -q --filter name=teder-trading-bot >/dev/null 2>&1; then
        echo "최근 컨테이너 로그 (50줄):"
        docker logs --tail=50 teder-trading-bot 2>&1 | tail -20
    else
        echo "컨테이너가 실행되지 않고 있습니다."
    fi
    echo ""

    # 네트워크 연결 테스트
    echo "=== 네트워크 연결 테스트 ==="
    echo "코인원 API 연결 테스트:"
    if curl -s --connect-timeout 10 https://api.coinone.co.kr/v2/ticker/?currency=usdt >/dev/null 2>&1; then
        echo "✅ 코인원 API 연결 성공"
    else
        echo "❌ 코인원 API 연결 실패"
    fi

    echo "DNS 해석 테스트:"
    if nslookup api.coinone.co.kr >/dev/null 2>&1; then
        echo "✅ DNS 해석 성공"
    else
        echo "❌ DNS 해석 실패"
    fi
    echo ""

    # 프로세스 정보
    echo "=== 프로세스 정보 ==="
    echo "Python 프로세스:"
    ps aux | grep -E "(python|main.py)" | grep -v grep
    echo ""
    echo "Docker 프로세스:"
    ps aux | grep docker | grep -v grep | head -5
    echo ""

    # 파일 시스템 권한
    echo "=== 파일 시스템 권한 ==="
    echo "프로젝트 디렉토리 권한:"
    ls -la "$PROJECT_DIR/" | head -10
    echo ""
    if [ -d "$PROJECT_DIR/logs" ]; then
        echo "로그 디렉토리 권한:"
        ls -la "$PROJECT_DIR/logs/" | head -5
    fi
    echo ""

    # 시스템 제한
    echo "=== 시스템 제한 ==="
    echo "파일 디스크립터 한도:"
    ulimit -n
    echo "프로세스 한도:"
    ulimit -u
    echo "메모리 한도:"
    ulimit -v
    echo ""

    # 시스템 로그 (주요 에러만)
    echo "=== 시스템 로그 (주요 에러) ==="
    echo "최근 시스템 에러 (10줄):"
    journalctl -p err --since "1 hour ago" -n 10 --no-pager 2>/dev/null || echo "journalctl을 사용할 수 없습니다."
    echo ""

    # 패키지 정보
    echo "=== 설치된 패키지 (주요) ==="
    if command -v pip3 >/dev/null 2>&1; then
        echo "Python 패키지 (주요):"
        pip3 list | grep -E "(requests|pandas|numpy|loguru|rich)" 2>/dev/null || echo "pip3을 사용할 수 없습니다."
    fi
    echo ""

    # 보안 정보
    echo "=== 보안 설정 ==="
    echo "방화벽 상태:"
    sudo ufw status 2>/dev/null || echo "ufw를 사용할 수 없습니다."
    echo ""
    echo "SSH 설정:"
    grep -E "(PermitRootLogin|PasswordAuthentication)" /etc/ssh/sshd_config 2>/dev/null | head -5 || echo "SSH 설정을 읽을 수 없습니다."
    echo ""

    # 마지막 업데이트 정보
    echo "=== 시스템 업데이트 정보 ==="
    echo "마지막 패키지 업데이트:"
    stat -c %y /var/lib/apt/lists/* 2>/dev/null | sort | tail -1 || echo "업데이트 정보를 확인할 수 없습니다."
    echo ""

    # 마무리
    echo "==================================================================="
    echo "디버그 정보 수집 완료: $(date)"
    echo "==================================================================="

} > "$DEBUG_FILE" 2>&1

# 디버그 파일 압축
cd "$DEBUG_DIR"
tar -czf "debug-info-$TIMESTAMP.tar.gz" "debug-info-$TIMESTAMP.txt"

# 추가 파일들 압축에 포함
if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
    cp "$PROJECT_DIR/docker-compose.yml" "docker-compose-$TIMESTAMP.yml"
fi

if [ -f "$PROJECT_DIR/.env" ]; then
    # .env 파일에서 민감한 정보를 마스킹하여 복사
    sed -E 's/(TOKEN|KEY|PASSWORD|SECRET)=.*/\1=***MASKED***/' "$PROJECT_DIR/.env" > "env-masked-$TIMESTAMP.txt"
fi

# 최종 압축
tar -czf "teder-debug-full-$TIMESTAMP.tar.gz" *-$TIMESTAMP.*

# 정리
rm -f *-$TIMESTAMP.txt *-$TIMESTAMP.yml

log_info "디버그 정보 수집이 완료되었습니다."
log_info "파일 위치: $DEBUG_DIR/teder-debug-full-$TIMESTAMP.tar.gz"
log_info ""
log_info "이 파일을 기술 지원팀에 전달하세요."
log_warn "파일에는 시스템 정보가 포함되어 있으므로 보안에 주의하세요."

# 파일 크기 출력
ls -lh "$DEBUG_DIR/teder-debug-full-$TIMESTAMP.tar.gz"

# 자동 정리 (30일 이상 된 디버그 파일)
find "$DEBUG_DIR" -name "teder-debug-full-*.tar.gz" -mtime +30 -delete 2>/dev/null || true

echo ""
echo "디버그 정보 수집 스크립트 실행 완료!"