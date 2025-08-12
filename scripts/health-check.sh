#!/bin/bash

# =================================================================
# Health Check Script for Teder Trading Bot
# =================================================================

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
readonly HEALTH_CHECK_URL="http://localhost:8080/health"
readonly TIMEOUT=10
readonly MAX_RETRIES=3

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO")  echo -e "${GREEN}[INFO]${NC} $message" ;;
        "WARN")  echo -e "${YELLOW}[WARN]${NC} $message" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $message" ;;
    esac
}

# Check if container is running
check_container_status() {
    local container_name="teder-trading-bot"
    
    if ! docker ps --format "table {{.Names}}" | grep -q "$container_name"; then
        log "ERROR" "Container $container_name is not running"
        return 1
    fi
    
    log "INFO" "Container $container_name is running"
    return 0
}

# Check container health status
check_container_health() {
    local container_name="teder-trading-bot"
    local health_status
    
    health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "unknown")
    
    case "$health_status" in
        "healthy")
            log "INFO" "Container health: $health_status"
            return 0
            ;;
        "unhealthy")
            log "ERROR" "Container health: $health_status"
            return 1
            ;;
        "starting")
            log "WARN" "Container health: $health_status"
            return 0
            ;;
        *)
            log "WARN" "Container health: $health_status"
            return 0
            ;;
    esac
}

# Check API connectivity
check_api_connectivity() {
    log "INFO" "Checking Coinone API connectivity..."
    
    # Use the same health check logic as the container
    local python_check='
import sys
import os
sys.path.append("/app")
try:
    from src.api.coinone_client import CoinoneClient
    client = CoinoneClient()
    result = client.get_ticker("usdt")
    if result and result.get("result") == "success":
        print("API connectivity: OK")
        sys.exit(0)
    else:
        print("API connectivity: FAILED")
        sys.exit(1)
except Exception as e:
    print(f"API connectivity: ERROR - {e}")
    sys.exit(1)
'
    
    if docker exec teder-trading-bot python -c "$python_check"; then
        log "INFO" "API connectivity check passed"
        return 0
    else
        log "ERROR" "API connectivity check failed"
        return 1
    fi
}

# Check disk space
check_disk_space() {
    log "INFO" "Checking disk space..."
    
    local usage
    usage=$(df "$PROJECT_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [[ $usage -gt 90 ]]; then
        log "ERROR" "Disk usage is critical: ${usage}%"
        return 1
    elif [[ $usage -gt 80 ]]; then
        log "WARN" "Disk usage is high: ${usage}%"
        return 0
    else
        log "INFO" "Disk usage is normal: ${usage}%"
        return 0
    fi
}

# Check memory usage
check_memory_usage() {
    log "INFO" "Checking memory usage..."
    
    local container_name="teder-trading-bot"
    local mem_usage
    
    if ! docker stats --no-stream --format "table {{.MemPerc}}" "$container_name" >/dev/null 2>&1; then
        log "WARN" "Cannot check memory usage - container not running"
        return 0
    fi
    
    mem_usage=$(docker stats --no-stream --format "{{.MemPerc}}" "$container_name" | sed 's/%//')
    
    if (( $(echo "$mem_usage > 90" | bc -l) )); then
        log "ERROR" "Memory usage is critical: ${mem_usage}%"
        return 1
    elif (( $(echo "$mem_usage > 80" | bc -l) )); then
        log "WARN" "Memory usage is high: ${mem_usage}%"
        return 0
    else
        log "INFO" "Memory usage is normal: ${mem_usage}%"
        return 0
    fi
}

# Check log file sizes
check_log_sizes() {
    log "INFO" "Checking log file sizes..."
    
    local log_dir="$PROJECT_DIR/logs"
    local max_size_mb=50
    local issues=0
    
    if [[ ! -d "$log_dir" ]]; then
        log "WARN" "Log directory does not exist: $log_dir"
        return 0
    fi
    
    while IFS= read -r -d '' logfile; do
        local size_mb
        size_mb=$(du -m "$logfile" | cut -f1)
        
        if [[ $size_mb -gt $max_size_mb ]]; then
            log "WARN" "Large log file detected: $(basename "$logfile") (${size_mb}MB)"
            ((issues++))
        fi
    done < <(find "$log_dir" -name "*.log" -print0)
    
    if [[ $issues -eq 0 ]]; then
        log "INFO" "All log files are within normal size limits"
    fi
    
    return 0
}

# Check trading bot status
check_trading_status() {
    log "INFO" "Checking trading bot status..."
    
    local container_name="teder-trading-bot"
    local last_log_time
    
    # Check if there are recent log entries (within last 5 minutes)
    last_log_time=$(docker logs --since=5m "$container_name" 2>/dev/null | tail -1 | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}' || echo "")
    
    if [[ -z "$last_log_time" ]]; then
        log "WARN" "No recent log activity from trading bot"
        return 0
    else
        log "INFO" "Trading bot is active (last log: $last_log_time)"
        return 0
    fi
}

# Main health check function
perform_health_check() {
    local exit_code=0
    local checks=0
    local failures=0
    
    log "INFO" "Starting comprehensive health check..."
    
    # Container status check
    ((checks++))
    if ! check_container_status; then
        ((failures++))
        exit_code=1
    fi
    
    # Container health check
    if [[ $exit_code -eq 0 ]]; then
        ((checks++))
        if ! check_container_health; then
            ((failures++))
            exit_code=1
        fi
    fi
    
    # API connectivity check
    if [[ $exit_code -eq 0 ]]; then
        ((checks++))
        if ! check_api_connectivity; then
            ((failures++))
            exit_code=1
        fi
    fi
    
    # System resource checks
    ((checks++))
    if ! check_disk_space; then
        ((failures++))
        exit_code=1
    fi
    
    ((checks++))
    if ! check_memory_usage; then
        ((failures++))
        exit_code=1
    fi
    
    # Log file checks
    ((checks++))
    check_log_sizes
    
    # Trading status check
    ((checks++))
    check_trading_status
    
    # Summary
    local passed=$((checks - failures))
    log "INFO" "Health check completed: $passed/$checks checks passed"
    
    if [[ $failures -gt 0 ]]; then
        log "ERROR" "$failures critical issues found"
    else
        log "INFO" "All critical health checks passed"
    fi
    
    return $exit_code
}

# Restart container if unhealthy
restart_if_unhealthy() {
    log "INFO" "Attempting to restart unhealthy container..."
    
    cd "$PROJECT_DIR"
    
    if docker-compose restart teder-bot; then
        log "INFO" "Container restart initiated"
        
        # Wait for container to be healthy
        local attempts=0
        local max_attempts=30
        
        while [[ $attempts -lt $max_attempts ]]; do
            sleep 10
            if check_container_health; then
                log "INFO" "Container is healthy after restart"
                return 0
            fi
            ((attempts++))
            log "INFO" "Waiting for container to be healthy... ($attempts/$max_attempts)"
        done
        
        log "ERROR" "Container did not become healthy after restart"
        return 1
    else
        log "ERROR" "Failed to restart container"
        return 1
    fi
}

# Main function
main() {
    local action="${1:-check}"
    local auto_restart="${2:-false}"
    
    cd "$PROJECT_DIR"
    
    case "$action" in
        "check")
            if perform_health_check; then
                exit 0
            else
                if [[ "$auto_restart" == "true" ]]; then
                    restart_if_unhealthy
                else
                    exit 1
                fi
            fi
            ;;
        "restart")
            restart_if_unhealthy
            ;;
        *)
            echo "Usage: $0 [check|restart] [auto_restart]"
            echo ""
            echo "Commands:"
            echo "  check      - Perform health check (default)"
            echo "  restart    - Restart container"
            echo ""
            echo "Options:"
            echo "  auto_restart - Automatically restart if unhealthy (true/false)"
            exit 1
            ;;
    esac
}

# Execute main function with arguments
main "$@"