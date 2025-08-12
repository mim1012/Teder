#!/bin/bash
# =============================================================================
# TEDER Trading Bot 로깅 설정 스크립트
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

# 로그 함수
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 로그 디렉토리 설정
setup_log_directories() {
    log_info "로그 디렉토리를 설정합니다..."
    
    local log_dirs=(
        "$PROJECT_DIR/logs"
        "$PROJECT_DIR/logs/archive"
        "$PROJECT_DIR/logs/trading"
        "$PROJECT_DIR/logs/system"
        "$PROJECT_DIR/logs/error"
    )
    
    for dir in "${log_dirs[@]}"; do
        mkdir -p "$dir"
        chmod 755 "$dir"
    done
    
    # 로그 인덱스 파일 생성
    cat > "$PROJECT_DIR/logs/README.md" << 'EOF'
# TEDER Trading Bot 로그 디렉토리

## 구조
- `trading/`: 거래 관련 로그
- `system/`: 시스템 모니터링 로그  
- `error/`: 에러 로그
- `archive/`: 압축된 과거 로그

## 로그 파일 설명
- `teder.log`: 메인 애플리케이션 로그
- `trading.log`: 거래 실행 로그
- `error.log`: 에러 로그
- `access.log`: API 접근 로그
- `performance.log`: 성능 메트릭 로그

## 로그 레벨
- DEBUG: 디버깅 정보
- INFO: 일반 정보
- WARNING: 경고 메시지
- ERROR: 에러 메시지
- CRITICAL: 심각한 에러

## 로그 보존 정책
- 일반 로그: 7일
- 에러 로그: 30일
- 거래 로그: 90일 (백업 포함)
EOF
}

# 로그 로테이션 설정
setup_log_rotation() {
    log_info "로그 로테이션을 설정합니다..."
    
    # Docker 컨테이너용 로그 로테이션 설정
    cat > "$PROJECT_DIR/logs/logrotate.conf" << 'EOF'
# TEDER Trading Bot 로그 로테이션 설정

/app/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 trader trader
    copytruncate
    postrotate
        # Docker 컨테이너에 로그 로테이션 신호 전송
        /usr/bin/docker kill -s SIGUSR1 $(docker ps -q --filter name=teder-trading-bot) 2>/dev/null || true
    endscript
}

/app/logs/trading/*.log {
    daily
    missingok
    rotate 90
    compress
    delaycompress
    notifempty
    create 644 trader trader
    copytruncate
    postrotate
        # 거래 로그는 더 오래 보관
        find /app/logs/archive -name "trading-*.gz" -mtime +90 -delete
    endscript
}

/app/logs/error/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 trader trader
    copytruncate
    postrotate
        # 에러 로그 알림 (선택사항)
        if [ -s /app/logs/error/error.log ]; then
            echo "New errors detected in TEDER Trading Bot" | logger -t teder-bot
        fi
    endscript
}

/app/logs/system/*.log {
    hourly
    missingok
    rotate 168  # 7일 * 24시간
    compress
    delaycompress
    notifempty
    create 644 trader trader
    copytruncate
}
EOF

    # 로그 로테이션 실행 스크립트
    cat > "$PROJECT_DIR/deploy/rotate-logs.sh" << 'EOF'
#!/bin/bash
# 로그 로테이션 실행 스크립트

set -e

LOG_DIR="/app/logs"
ARCHIVE_DIR="/app/logs/archive"
DATE=$(date +%Y%m%d_%H%M%S)

# 아카이브 디렉토리 생성
mkdir -p "$ARCHIVE_DIR"

# 큰 로그 파일 압축 및 아카이브
find "$LOG_DIR" -name "*.log" -size +100M -exec gzip {} \;
find "$LOG_DIR" -name "*.log.gz" -exec mv {} "$ARCHIVE_DIR/" \;

# 30일 이상 된 아카이브 파일 삭제
find "$ARCHIVE_DIR" -name "*.gz" -mtime +30 -delete

# 로그 디렉토리 용량 확인
USAGE=$(du -sm "$LOG_DIR" | cut -f1)
if [ "$USAGE" -gt 1000 ]; then  # 1GB 이상
    echo "WARNING: Log directory size is ${USAGE}MB"
    # 오래된 로그 파일 정리
    find "$LOG_DIR" -name "*.log" -mtime +7 -delete
fi

echo "Log rotation completed at $(date)"
EOF

    chmod +x "$PROJECT_DIR/deploy/rotate-logs.sh"
}

# 로그 모니터링 설정
setup_log_monitoring() {
    log_info "로그 모니터링을 설정합니다..."
    
    # 로그 분석 스크립트
    cat > "$PROJECT_DIR/deploy/analyze-logs.sh" << 'EOF'
#!/bin/bash
# 로그 분석 스크립트

set -e

LOG_DIR="/app/logs"
REPORT_FILE="/app/logs/log-analysis-$(date +%Y%m%d).txt"

echo "=== TEDER Trading Bot 로그 분석 보고서 ===" > "$REPORT_FILE"
echo "생성 시간: $(date)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 에러 통계
echo "=== 에러 통계 (최근 24시간) ===" >> "$REPORT_FILE"
if [ -f "$LOG_DIR/error.log" ]; then
    grep -c "ERROR" "$LOG_DIR/error.log" 2>/dev/null || echo "0" | \
    awk '{print "총 에러 수: " $1}' >> "$REPORT_FILE"
    
    grep -c "CRITICAL" "$LOG_DIR/error.log" 2>/dev/null || echo "0" | \
    awk '{print "심각한 에러 수: " $1}' >> "$REPORT_FILE"
else
    echo "에러 로그 파일 없음" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# 거래 통계
echo "=== 거래 통계 (최근 24시간) ===" >> "$REPORT_FILE"
if [ -f "$LOG_DIR/trading/trading.log" ]; then
    grep -c "매수 체결" "$LOG_DIR/trading/trading.log" 2>/dev/null || echo "0" | \
    awk '{print "매수 건수: " $1}' >> "$REPORT_FILE"
    
    grep -c "매도 체결" "$LOG_DIR/trading/trading.log" 2>/dev/null || echo "0" | \
    awk '{print "매도 건수: " $1}' >> "$REPORT_FILE"
    
    grep -c "익절" "$LOG_DIR/trading/trading.log" 2>/dev/null || echo "0" | \
    awk '{print "익절 건수: " $1}' >> "$REPORT_FILE"
    
    grep -c "손절" "$LOG_DIR/trading/trading.log" 2>/dev/null || echo "0" | \
    awk '{print "손절 건수: " $1}' >> "$REPORT_FILE"
else
    echo "거래 로그 파일 없음" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# API 호출 통계
echo "=== API 호출 통계 (최근 24시간) ===" >> "$REPORT_FILE"
if [ -f "$LOG_DIR/access.log" ]; then
    grep -c "API_CALL" "$LOG_DIR/access.log" 2>/dev/null || echo "0" | \
    awk '{print "총 API 호출 수: " $1}' >> "$REPORT_FILE"
    
    grep -c "API_ERROR" "$LOG_DIR/access.log" 2>/dev/null || echo "0" | \
    awk '{print "API 에러 수: " $1}' >> "$REPORT_FILE"
else
    echo "API 로그 파일 없음" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# 시스템 리소스
echo "=== 시스템 리소스 ===" >> "$REPORT_FILE"
echo "디스크 사용량:" >> "$REPORT_FILE"
df -h "$LOG_DIR" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "메모리 사용량:" >> "$REPORT_FILE"
free -h >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 최근 에러 메시지 (상위 10개)
echo "=== 최근 에러 메시지 (상위 10개) ===" >> "$REPORT_FILE"
if [ -f "$LOG_DIR/error.log" ]; then
    tail -100 "$LOG_DIR/error.log" | grep "ERROR\|CRITICAL" | tail -10 >> "$REPORT_FILE"
else
    echo "에러 로그 없음" >> "$REPORT_FILE"
fi

echo "로그 분석 완료: $REPORT_FILE"
EOF

    chmod +x "$PROJECT_DIR/deploy/analyze-logs.sh"
    
    # 로그 알림 스크립트
    cat > "$PROJECT_DIR/deploy/log-alert.sh" << 'EOF'
#!/bin/bash
# 로그 기반 알림 스크립트

set -e

LOG_DIR="/app/logs"
ALERT_FILE="/tmp/teder-alerts.tmp"

# 알림 조건 확인
check_critical_errors() {
    local count=$(grep -c "CRITICAL" "$LOG_DIR/error.log" 2>/dev/null || echo "0")
    if [ "$count" -gt 0 ]; then
        echo "CRITICAL: $count critical errors found" >> "$ALERT_FILE"
    fi
}

check_high_error_rate() {
    local errors=$(grep -c "ERROR" "$LOG_DIR/error.log" 2>/dev/null || echo "0")
    local total=$(wc -l < "$LOG_DIR/teder.log" 2>/dev/null || echo "1")
    local rate=$((errors * 100 / total))
    
    if [ "$rate" -gt 10 ]; then
        echo "WARNING: High error rate detected: ${rate}%" >> "$ALERT_FILE"
    fi
}

check_disk_space() {
    local usage=$(df "$LOG_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$usage" -gt 90 ]; then
        echo "WARNING: Log disk usage is ${usage}%" >> "$ALERT_FILE"
    fi
}

check_api_failures() {
    local failures=$(grep -c "API_ERROR" "$LOG_DIR/access.log" 2>/dev/null || echo "0")
    if [ "$failures" -gt 50 ]; then
        echo "WARNING: High API failure rate: $failures failures" >> "$ALERT_FILE"
    fi
}

# 알림 전송
send_alerts() {
    if [ -f "$ALERT_FILE" ] && [ -s "$ALERT_FILE" ]; then
        echo "TEDER Trading Bot Alerts at $(date):"
        cat "$ALERT_FILE"
        
        # 여기에 실제 알림 전송 로직 추가
        # 예: 이메일, 슬랙, 텔레그램 등
        
        # 알림 파일 정리
        rm "$ALERT_FILE"
    fi
}

# 메인 실행
main() {
    # 알림 파일 초기화
    > "$ALERT_FILE"
    
    check_critical_errors
    check_high_error_rate
    check_disk_space
    check_api_failures
    
    send_alerts
}

main "$@"
EOF

    chmod +x "$PROJECT_DIR/deploy/log-alert.sh"
}

# 로그 설정 검증
validate_log_config() {
    log_info "로그 설정을 검증합니다..."
    
    # 디렉토리 권한 확인
    if [ ! -w "$PROJECT_DIR/logs" ]; then
        log_error "로그 디렉토리에 쓰기 권한이 없습니다: $PROJECT_DIR/logs"
        return 1
    fi
    
    # 로그 로테이션 설정 확인
    if [ ! -f "$PROJECT_DIR/logs/logrotate.conf" ]; then
        log_error "로그 로테이션 설정 파일이 없습니다"
        return 1
    fi
    
    # 스크립트 실행 권한 확인
    local scripts=(
        "$PROJECT_DIR/deploy/rotate-logs.sh"
        "$PROJECT_DIR/deploy/analyze-logs.sh"
        "$PROJECT_DIR/deploy/log-alert.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ ! -x "$script" ]; then
            log_error "스크립트 실행 권한이 없습니다: $script"
            return 1
        fi
    done
    
    log_info "로그 설정 검증 완료"
}

# 로그 크론 작업 설정
setup_log_cron() {
    log_info "로그 크론 작업을 설정합니다..."
    
    # 크론 설정 파일 생성
    cat > "$PROJECT_DIR/deploy/log-crontab" << 'EOF'
# TEDER Trading Bot 로그 관리 크론 작업

# 매일 02:00에 로그 로테이션 실행
0 2 * * * /app/deploy/rotate-logs.sh >> /app/logs/cron.log 2>&1

# 매시간 로그 분석 실행
0 * * * * /app/deploy/analyze-logs.sh >> /app/logs/analysis.log 2>&1

# 5분마다 로그 알림 확인
*/5 * * * * /app/deploy/log-alert.sh >> /app/logs/alert.log 2>&1

# 매주 일요일 03:00에 오래된 로그 정리
0 3 * * 0 find /app/logs -name "*.log" -mtime +30 -delete >> /app/logs/cleanup.log 2>&1
EOF
    
    log_info "크론 작업 설정 완료"
    log_info "컨테이너에서 다음 명령으로 크론 작업을 등록하세요:"
    log_info "  crontab /app/deploy/log-crontab"
}

# 메인 실행 함수
main() {
    log_info "TEDER Trading Bot 로깅 설정을 시작합니다..."
    
    setup_log_directories
    setup_log_rotation
    setup_log_monitoring
    setup_log_cron
    validate_log_config
    
    log_info "로깅 설정이 완료되었습니다!"
    log_info ""
    log_info "설정된 기능:"
    log_info "  - 자동 로그 로테이션"
    log_info "  - 로그 분석 및 리포트"
    log_info "  - 실시간 로그 알림"
    log_info "  - 자동 로그 정리"
    log_info ""
    log_info "로그 관리 명령어:"
    log_info "  - 로그 로테이션: ./deploy/rotate-logs.sh"
    log_info "  - 로그 분석: ./deploy/analyze-logs.sh"
    log_info "  - 알림 확인: ./deploy/log-alert.sh"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi