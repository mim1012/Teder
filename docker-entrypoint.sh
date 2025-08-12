#!/bin/bash
# =============================================================================
# TEDER Trading Bot Docker Entrypoint Script
# =============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [ "$DEBUG_MODE" = "true" ]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# 환경 검증
validate_environment() {
    log_info "환경 변수 검증 중..."
    
    # 필수 환경 변수 확인
    required_vars=(
        "COINONE_ACCESS_TOKEN"
        "COINONE_SECRET_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "필수 환경 변수 $var 가 설정되지 않았습니다."
            exit 1
        fi
    done
    
    # API 키 형식 검증
    if [ "${#COINONE_ACCESS_TOKEN}" -lt 10 ]; then
        log_error "COINONE_ACCESS_TOKEN이 너무 짧습니다."
        exit 1
    fi
    
    if [ "${#COINONE_SECRET_KEY}" -lt 10 ]; then
        log_error "COINONE_SECRET_KEY가 너무 짧습니다."
        exit 1
    fi
    
    log_info "환경 변수 검증 완료"
}

# 디렉토리 생성
create_directories() {
    log_info "필요한 디렉토리 생성 중..."
    
    directories=(
        "/app/logs"
        "/app/data"
        "/app/backups"
        "${DATA_PATH:-/app/data}"
        "${BACKUP_PATH:-/app/backups}"
        "${LOG_PATH:-/app/logs}"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_debug "디렉토리 생성: $dir"
        fi
    done
    
    # 권한 설정
    chmod 755 /app/logs /app/data /app/backups
    
    log_info "디렉토리 생성 완료"
}

# 헬스체크 파일 생성
setup_healthcheck() {
    log_info "헬스체크 설정 중..."
    
    # 기본 헬스체크 스크립트가 없다면 생성
    if [ ! -f "/app/healthcheck.sh" ]; then
        cat > /app/healthcheck.sh << 'EOF'
#!/bin/bash
# 간단한 헬스체크 스크립트

# Python 프로세스 확인
if ! pgrep -f "python.*main.py" > /dev/null; then
    echo "Python 프로세스를 찾을 수 없습니다."
    exit 1
fi

# API 연결 테스트
python -c "
import requests
import sys
try:
    response = requests.get('https://api.coinone.co.kr/v2/ticker/?currency=usdt', timeout=10)
    if response.status_code == 200:
        sys.exit(0)
    else:
        sys.exit(1)
except Exception as e:
    print(f'헬스체크 실패: {e}')
    sys.exit(1)
"
EOF
        chmod +x /app/healthcheck.sh
    fi
    
    log_info "헬스체크 설정 완료"
}

# 로그 설정
setup_logging() {
    log_info "로그 설정 중..."
    
    # 로그 로테이션 설정
    if [ ! -f "/etc/logrotate.d/teder" ]; then
        cat > /tmp/teder-logrotate << EOF
${LOG_PATH:-/app/logs}/*.log {
    daily
    missingok
    rotate ${LOG_BACKUP_COUNT:-5}
    compress
    delaycompress
    notifempty
    create 644 trader trader
    postrotate
        /usr/bin/killall -SIGUSR1 python || true
    endscript
}
EOF
        # logrotate 설정 (권한이 있다면)
        if command -v logrotate >/dev/null 2>&1; then
            sudo cp /tmp/teder-logrotate /etc/logrotate.d/teder 2>/dev/null || true
        fi
    fi
    
    log_info "로그 설정 완료"
}

# 권한 확인
check_permissions() {
    log_info "권한 확인 중..."
    
    # 쓰기 권한 확인
    test_dirs=("/app/logs" "/app/data" "/app/backups")
    
    for dir in "${test_dirs[@]}"; do
        if [ ! -w "$dir" ]; then
            log_error "$dir 디렉토리에 쓰기 권한이 없습니다."
            exit 1
        fi
    done
    
    log_info "권한 확인 완료"
}

# 의존성 확인
check_dependencies() {
    log_info "의존성 확인 중..."
    
    # Python 모듈 확인
    required_modules=(
        "requests"
        "pandas"
        "numpy"
        "loguru"
        "rich"
    )
    
    for module in "${required_modules[@]}"; do
        if ! python -c "import $module" 2>/dev/null; then
            log_error "Python 모듈 $module 을 찾을 수 없습니다."
            exit 1
        fi
    done
    
    log_info "의존성 확인 완료"
}

# 백업 설정
setup_backup() {
    log_info "백업 설정 중..."
    
    # 백업 스크립트 생성
    cat > /app/backup.sh << 'EOF'
#!/bin/bash
# 자동 백업 스크립트

BACKUP_DIR="${BACKUP_PATH:-/app/backups}"
DATA_DIR="${DATA_PATH:-/app/data}"
LOG_DIR="${LOG_PATH:-/app/logs}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 백업 생성
tar -czf "$BACKUP_DIR/teder_backup_$TIMESTAMP.tar.gz" \
    -C /app \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    data/ logs/ config/ 2>/dev/null || true

# 오래된 백업 삭제 (7일 이상)
find "$BACKUP_DIR" -name "teder_backup_*.tar.gz" -mtime +7 -delete 2>/dev/null || true

echo "백업 완료: teder_backup_$TIMESTAMP.tar.gz"
EOF
    
    chmod +x /app/backup.sh
    
    log_info "백업 설정 완료"
}

# 시그널 핸들러 설정
setup_signal_handlers() {
    log_info "시그널 핸들러 설정 중..."
    
    # 종료 시그널 처리
    trap 'log_info "종료 신호를 받았습니다. 안전하게 종료합니다..."; kill -TERM $child_pid 2>/dev/null; wait $child_pid' TERM INT
    
    log_info "시그널 핸들러 설정 완료"
}

# 네트워크 연결 확인
check_network() {
    log_info "네트워크 연결 확인 중..."
    
    # 코인원 API 연결 테스트
    if ! curl -s --connect-timeout 10 https://api.coinone.co.kr/v2/ticker/?currency=usdt >/dev/null; then
        log_error "코인원 API에 연결할 수 없습니다."
        exit 1
    fi
    
    log_info "네트워크 연결 확인 완료"
}

# 메인 실행 함수
main() {
    log_info "==================================================="
    log_info "TEDER 코인원 자동매매 봇 시작"
    log_info "==================================================="
    log_info "컨테이너: ${CONTAINER_NAME:-teder-trading-bot}"
    log_info "버전: $(python --version)"
    log_info "시간: $(date)"
    log_info "거래 모드: ${TRADING_MODE:-dry_run}"
    log_info "==================================================="
    
    # 초기화 단계
    validate_environment
    create_directories
    setup_healthcheck
    setup_logging
    check_permissions
    check_dependencies
    setup_backup
    setup_signal_handlers
    check_network
    
    log_info "초기화 완료. 메인 애플리케이션을 시작합니다..."
    
    # 백그라운드 작업 시작
    if [ "${ENABLE_BACKUP:-false}" = "true" ]; then
        # 일일 백업 (백그라운드)
        (while true; do
            sleep 86400  # 24시간
            /app/backup.sh
        done) &
    fi
    
    # 메인 애플리케이션 실행
    exec "$@" &
    child_pid=$!
    
    # 자식 프로세스 대기
    wait $child_pid
    exit_code=$?
    
    log_info "애플리케이션이 종료되었습니다. (Exit code: $exit_code)"
    exit $exit_code
}

# 스크립트가 직접 실행될 때만 main 함수 호출
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi