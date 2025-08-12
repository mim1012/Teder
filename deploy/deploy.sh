#!/bin/bash
# =============================================================================
# TEDER Trading Bot 배포 스크립트
# =============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
ENV_FILE="$PROJECT_DIR/.env"
BACKUP_DIR="$PROJECT_DIR/backups"

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

log_success() {
    echo -e "${CYAN}[SUCCESS]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 사용법 출력
usage() {
    cat << EOF
TEDER Trading Bot 배포 스크립트

사용법:
    $0 [COMMAND] [OPTIONS]

Commands:
    build       Docker 이미지 빌드
    start       서비스 시작
    stop        서비스 중지
    restart     서비스 재시작
    status      서비스 상태 확인
    logs        로그 보기
    backup      데이터 백업
    restore     데이터 복원
    update      애플리케이션 업데이트
    clean       사용하지 않는 리소스 정리
    health      헬스체크 실행
    setup       초기 설정

Options:
    -e, --env FILE      환경 변수 파일 지정 (기본: .env)
    -f, --file FILE     docker-compose 파일 지정
    -v, --verbose       상세 출력
    -h, --help          도움말 출력

예시:
    $0 setup                    # 초기 설정
    $0 build                    # 이미지 빌드
    $0 start                    # 서비스 시작
    $0 logs -f                  # 실시간 로그 보기
    $0 backup                   # 데이터 백업
    $0 update                   # 애플리케이션 업데이트

EOF
}

# 전제조건 확인
check_prerequisites() {
    log_step "전제조건 확인 중..."
    
    # Docker 확인
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker가 설치되지 않았습니다."
        exit 1
    fi
    
    # Docker Compose 확인
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "Docker Compose가 설치되지 않았습니다."
        exit 1
    fi
    
    # 프로젝트 디렉토리 확인
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "docker-compose.yml 파일을 찾을 수 없습니다: $COMPOSE_FILE"
        exit 1
    fi
    
    log_info "전제조건 확인 완료"
}

# 환경 파일 확인
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log_warn ".env 파일이 없습니다. .env.example을 복사해서 설정하세요."
        if [ -f "$PROJECT_DIR/.env.example" ]; then
            log_info ".env.example을 .env로 복사합니다..."
            cp "$PROJECT_DIR/.env.example" "$ENV_FILE"
            log_warn "⚠️  .env 파일을 편집하여 실제 설정값을 입력하세요!"
            log_warn "특히 다음 항목들을 반드시 설정하세요:"
            log_warn "  - COINONE_ACCESS_TOKEN"
            log_warn "  - COINONE_SECRET_KEY"
            log_warn "  - TRADING_MODE (dry_run 또는 live)"
            echo
            read -p "계속하시겠습니까? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        else
            log_error ".env.example 파일도 찾을 수 없습니다."
            exit 1
        fi
    fi
}

# 초기 설정
setup() {
    log_step "초기 설정을 시작합니다..."
    
    check_prerequisites
    check_env_file
    
    # 필요한 디렉토리 생성
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/data"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$PROJECT_DIR/monitoring/prometheus"
    mkdir -p "$PROJECT_DIR/monitoring/grafana/dashboards"
    mkdir -p "$PROJECT_DIR/monitoring/grafana/datasources"
    mkdir -p "$PROJECT_DIR/monitoring/fluentd"
    
    # Prometheus 설정 파일 생성
    create_prometheus_config
    
    # Grafana 설정 파일 생성
    create_grafana_config
    
    # Fluentd 설정 파일 생성
    create_fluentd_config
    
    log_success "초기 설정이 완료되었습니다!"
    log_info "다음 명령으로 서비스를 시작할 수 있습니다:"
    log_info "  $0 build && $0 start"
}

# Prometheus 설정 생성
create_prometheus_config() {
    local config_file="$PROJECT_DIR/monitoring/prometheus.yml"
    if [ ! -f "$config_file" ]; then
        cat > "$config_file" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'teder-trading-bot'
    static_configs:
      - targets: ['teder-trading-bot:9100']
    scrape_interval: 30s
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          # - alertmanager:9093
EOF
        log_info "Prometheus 설정 파일을 생성했습니다: $config_file"
    fi
}

# Grafana 설정 생성
create_grafana_config() {
    local datasource_file="$PROJECT_DIR/monitoring/grafana/datasources/prometheus.yml"
    mkdir -p "$(dirname "$datasource_file")"
    
    if [ ! -f "$datasource_file" ]; then
        cat > "$datasource_file" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF
        log_info "Grafana 데이터소스 설정을 생성했습니다: $datasource_file"
    fi
    
    local dashboard_file="$PROJECT_DIR/monitoring/grafana/dashboards/dashboard.yml"
    if [ ! -f "$dashboard_file" ]; then
        cat > "$dashboard_file" << 'EOF'
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF
        log_info "Grafana 대시보드 설정을 생성했습니다: $dashboard_file"
    fi
}

# Fluentd 설정 생성
create_fluentd_config() {
    local config_file="$PROJECT_DIR/monitoring/fluentd/fluent.conf"
    mkdir -p "$(dirname "$config_file")"
    
    if [ ! -f "$config_file" ]; then
        cat > "$config_file" << 'EOF'
<source>
  @type tail
  path /var/log/teder/*.log
  pos_file /var/log/fluentd/teder.log.pos
  tag teder.trading
  format json
  time_format %Y-%m-%d %H:%M:%S
</source>

<match teder.**>
  @type copy
  <store>
    @type file
    path /var/log/fluentd/teder
    append true
    time_slice_format %Y%m%d
    time_slice_wait 10m
    time_format %Y%m%dT%H%M%S%z
    compress gzip
  </store>
  <store>
    @type stdout
  </store>
</match>
EOF
        log_info "Fluentd 설정 파일을 생성했습니다: $config_file"
    fi
}

# Docker 이미지 빌드
build() {
    log_step "Docker 이미지를 빌드합니다..."
    
    cd "$PROJECT_DIR"
    
    # 빌드 전 정리
    docker system prune -f >/dev/null 2>&1 || true
    
    # 이미지 빌드
    docker-compose build --no-cache
    
    log_success "Docker 이미지 빌드 완료"
}

# 서비스 시작
start() {
    log_step "서비스를 시작합니다..."
    
    check_env_file
    cd "$PROJECT_DIR"
    
    # 서비스 시작
    docker-compose up -d
    
    # 시작 대기
    log_info "서비스 시작을 대기합니다..."
    sleep 10
    
    # 상태 확인
    status
    
    log_success "서비스가 시작되었습니다!"
    log_info "모니터링 대시보드: http://localhost:3000 (admin/admin123)"
    log_info "Prometheus: http://localhost:9090"
    log_info "애플리케이션 상태: http://localhost:8000"
}

# 서비스 중지
stop() {
    log_step "서비스를 중지합니다..."
    
    cd "$PROJECT_DIR"
    
    # 안전한 종료를 위해 시그널 전송
    docker-compose kill -s SIGTERM
    
    # 컨테이너 중지
    docker-compose down
    
    log_success "서비스가 중지되었습니다."
}

# 서비스 재시작
restart() {
    log_step "서비스를 재시작합니다..."
    
    stop
    sleep 5
    start
    
    log_success "서비스 재시작 완료"
}

# 서비스 상태 확인
status() {
    log_step "서비스 상태를 확인합니다..."
    
    cd "$PROJECT_DIR"
    
    echo "=== Docker Compose 서비스 상태 ==="
    docker-compose ps
    
    echo
    echo "=== 컨테이너 리소스 사용량 ==="
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
    
    echo
    echo "=== 헬스체크 상태 ==="
    docker-compose exec -T teder-trading-bot /app/healthcheck.sh 2>/dev/null && \
        log_success "애플리케이션 상태: 정상" || \
        log_error "애플리케이션 상태: 비정상"
}

# 로그 보기
logs() {
    log_step "로그를 확인합니다..."
    
    cd "$PROJECT_DIR"
    
    if [ "$1" = "-f" ] || [ "$1" = "--follow" ]; then
        docker-compose logs -f
    else
        docker-compose logs --tail=100
    fi
}

# 데이터 백업
backup() {
    log_step "데이터를 백업합니다..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/teder_backup_$timestamp.tar.gz"
    
    # 백업 디렉토리 생성
    mkdir -p "$BACKUP_DIR"
    
    # 실행 중인 컨테이너에서 백업 실행
    if docker-compose ps -q teder-trading-bot >/dev/null 2>&1; then
        docker-compose exec -T teder-trading-bot /app/backup.sh
    fi
    
    # 호스트에서 추가 백업
    tar -czf "$backup_file" \
        -C "$PROJECT_DIR" \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='logs/*.log' \
        data/ config/ .env 2>/dev/null || true
    
    log_success "백업 완료: $backup_file"
    
    # 오래된 백업 정리 (30일 이상)
    find "$BACKUP_DIR" -name "teder_backup_*.tar.gz" -mtime +30 -delete 2>/dev/null || true
}

# 데이터 복원
restore() {
    log_step "데이터를 복원합니다..."
    
    if [ -z "$1" ]; then
        log_error "복원할 백업 파일을 지정하세요."
        log_info "사용법: $0 restore <backup_file>"
        log_info "사용 가능한 백업 파일:"
        ls -la "$BACKUP_DIR"/teder_backup_*.tar.gz 2>/dev/null || log_warn "백업 파일이 없습니다."
        exit 1
    fi
    
    local backup_file="$1"
    if [ ! -f "$backup_file" ]; then
        backup_file="$BACKUP_DIR/$1"
    fi
    
    if [ ! -f "$backup_file" ]; then
        log_error "백업 파일을 찾을 수 없습니다: $backup_file"
        exit 1
    fi
    
    # 확인
    read -p "정말로 데이터를 복원하시겠습니까? 기존 데이터가 덮어씌워집니다. (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "복원이 취소되었습니다."
        exit 0
    fi
    
    # 서비스 중지
    stop
    
    # 데이터 복원
    tar -xzf "$backup_file" -C "$PROJECT_DIR"
    
    log_success "데이터 복원 완료: $backup_file"
    log_info "서비스를 다시 시작하세요: $0 start"
}

# 애플리케이션 업데이트
update() {
    log_step "애플리케이션을 업데이트합니다..."
    
    # Git 저장소에서 최신 코드 가져오기 (선택사항)
    if [ -d "$PROJECT_DIR/.git" ]; then
        log_info "Git에서 최신 코드를 가져옵니다..."
        cd "$PROJECT_DIR"
        git pull origin main || log_warn "Git pull 실패. 수동으로 코드를 확인하세요."
    fi
    
    # 백업 생성
    backup
    
    # 이미지 재빌드
    build
    
    # 서비스 재시작
    restart
    
    log_success "애플리케이션 업데이트 완료"
}

# 정리
clean() {
    log_step "사용하지 않는 리소스를 정리합니다..."
    
    # 중지된 컨테이너 정리
    docker container prune -f
    
    # 사용하지 않는 이미지 정리
    docker image prune -f
    
    # 사용하지 않는 볼륨 정리 (주의!)
    read -p "사용하지 않는 Docker 볼륨도 정리하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume prune -f
    fi
    
    # 사용하지 않는 네트워크 정리
    docker network prune -f
    
    # 시스템 정리
    docker system prune -f
    
    log_success "리소스 정리 완료"
}

# 헬스체크
health() {
    log_step "헬스체크를 실행합니다..."
    
    cd "$PROJECT_DIR"
    
    # 컨테이너 상태 확인
    if ! docker-compose ps | grep -q "Up"; then
        log_error "서비스가 실행되지 않고 있습니다."
        exit 1
    fi
    
    # 애플리케이션 헬스체크
    if docker-compose exec -T teder-trading-bot /app/healthcheck.sh; then
        log_success "헬스체크 통과"
    else
        log_error "헬스체크 실패"
        exit 1
    fi
    
    # 디스크 사용량 확인
    df -h "$PROJECT_DIR" | tail -1 | awk '{
        if(substr($5,1,length($5)-1) > 90) {
            print "⚠️  디스크 사용량이 높습니다: " $5
        } else {
            print "✅ 디스크 사용량: " $5
        }
    }'
    
    # 메모리 사용량 확인
    free -h | awk 'NR==2{
        if(substr($3,1,length($3)-1) > 80) {
            print "⚠️  메모리 사용량이 높습니다: " $3 "/" $2
        } else {
            print "✅ 메모리 사용량: " $3 "/" $2
        }
    }'
}

# 메인 함수
main() {
    local command="$1"
    shift || true
    
    case "$command" in
        setup)
            setup "$@"
            ;;
        build)
            check_prerequisites
            build "$@"
            ;;
        start)
            check_prerequisites
            start "$@"
            ;;
        stop)
            stop "$@"
            ;;
        restart)
            check_prerequisites
            restart "$@"
            ;;
        status)
            status "$@"
            ;;
        logs)
            logs "$@"
            ;;
        backup)
            backup "$@"
            ;;
        restore)
            restore "$@"
            ;;
        update)
            check_prerequisites
            update "$@"
            ;;
        clean)
            clean "$@"
            ;;
        health)
            health "$@"
            ;;
        -h|--help|help)
            usage
            ;;
        "")
            log_error "명령을 지정하세요."
            usage
            exit 1
            ;;
        *)
            log_error "알 수 없는 명령: $command"
            usage
            exit 1
            ;;
    esac
}

# 스크립트 실행
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi