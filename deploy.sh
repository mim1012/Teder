#!/bin/bash

# =================================================================
# Teder Crypto Trading Bot - Production Deployment Script
# =================================================================

set -euo pipefail  # Exit on error, undefined variables, pipe failures

# Script configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_NAME="teder-trading-bot"
readonly DEFAULT_ENV="production"
readonly LOG_FILE="/tmp/teder-deploy-$(date +%Y%m%d-%H%M%S).log"

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# =================================================================
# Utility Functions
# =================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO")  echo -e "${GREEN}[INFO]${NC} $message" | tee -a "$LOG_FILE" ;;
        "WARN")  echo -e "${YELLOW}[WARN]${NC} $message" | tee -a "$LOG_FILE" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $message" | tee -a "$LOG_FILE" ;;
        "DEBUG") echo -e "${BLUE}[DEBUG]${NC} $message" | tee -a "$LOG_FILE" ;;
    esac
}

show_usage() {
    cat << EOF
Teder Crypto Trading Bot - Deployment Script

Usage: $0 [OPTIONS] COMMAND

Commands:
    setup       Initial VPS setup with dependencies
    build       Build Docker images
    deploy      Deploy the trading bot
    start       Start services
    stop        Stop services
    restart     Restart services
    status      Show service status
    logs        Show logs
    backup      Create backup
    restore     Restore from backup
    cleanup     Clean unused Docker resources
    update      Update and redeploy

Options:
    -e, --env ENV           Environment (production, staging, development)
    -f, --force             Force operation without confirmation
    -v, --verbose           Verbose output
    -h, --help              Show this help message

Examples:
    $0 setup                    # Initial VPS setup
    $0 --env production deploy  # Deploy to production
    $0 start                    # Start services
    $0 logs --follow            # Follow logs
    $0 backup                   # Create backup

EOF
}

check_requirements() {
    local requirements=("docker" "docker-compose" "git" "curl")
    local missing=()
    
    log "INFO" "Checking system requirements..."
    
    for req in "${requirements[@]}"; do
        if ! command -v "$req" >/dev/null 2>&1; then
            missing+=("$req")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log "ERROR" "Missing requirements: ${missing[*]}"
        return 1
    fi
    
    log "INFO" "All requirements satisfied"
    return 0
}

setup_directories() {
    log "INFO" "Setting up directory structure..."
    
    local dirs=(
        "logs"
        "data"
        "config"
        "scripts"
        "backups"
        "data/redis"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log "INFO" "Created directory: $dir"
        fi
    done
    
    # Set proper permissions
    chmod 755 logs data config scripts backups
    chmod 700 data/redis  # More restrictive for Redis data
}

# =================================================================
# Main Commands
# =================================================================

setup_vps() {
    log "INFO" "Starting VPS setup..."
    
    # Update system
    log "INFO" "Updating system packages..."
    sudo apt-get update && sudo apt-get upgrade -y
    
    # Install Docker
    if ! command -v docker >/dev/null 2>&1; then
        log "INFO" "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker "$USER"
        rm get-docker.sh
    fi
    
    # Install Docker Compose
    if ! command -v docker-compose >/dev/null 2>&1; then
        log "INFO" "Installing Docker Compose..."
        local compose_version="2.21.0"
        sudo curl -L "https://github.com/docker/compose/releases/download/v${compose_version}/docker-compose-$(uname -s)-$(uname -m)" \
            -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    # Install additional tools
    log "INFO" "Installing additional tools..."
    sudo apt-get install -y \
        htop \
        ncdu \
        tree \
        jq \
        fail2ban \
        ufw \
        logrotate
    
    # Configure firewall
    setup_firewall
    
    # Configure fail2ban
    setup_fail2ban
    
    # Setup directories
    setup_directories
    
    log "INFO" "VPS setup completed successfully!"
    log "WARN" "Please log out and back in for Docker permissions to take effect"
}

setup_firewall() {
    log "INFO" "Configuring UFW firewall..."
    
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # SSH access
    sudo ufw allow ssh
    
    # HTTP/HTTPS for monitoring (optional)
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Monitoring ports (optional)
    sudo ufw allow 9100/tcp  # Node Exporter
    
    sudo ufw --force enable
    log "INFO" "Firewall configured and enabled"
}

setup_fail2ban() {
    log "INFO" "Configuring Fail2Ban..."
    
    sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s
backend = %(sshd_backend)s
maxretry = 3
bantime = 3600
EOF

    sudo systemctl enable fail2ban
    sudo systemctl restart fail2ban
    log "INFO" "Fail2Ban configured and started"
}

build_images() {
    log "INFO" "Building Docker images..."
    
    # Set build arguments
    export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    export VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    export VERSION=$(git describe --tags --exact-match 2>/dev/null || echo "latest")
    
    log "INFO" "Build info: VERSION=$VERSION, VCS_REF=$VCS_REF, BUILD_DATE=$BUILD_DATE"
    
    # Build with cache optimization
    docker-compose build --parallel --pull
    
    log "INFO" "Images built successfully"
}

deploy_services() {
    log "INFO" "Deploying services..."
    
    # Validate environment file
    if [[ ! -f ".env" ]]; then
        log "ERROR" ".env file not found. Please create it from .env.example"
        return 1
    fi
    
    # Build images
    build_images
    
    # Create necessary directories
    setup_directories
    
    # Deploy with health checks
    docker-compose up -d --remove-orphans
    
    # Wait for services to be healthy
    wait_for_health
    
    log "INFO" "Deployment completed successfully"
}

wait_for_health() {
    local max_attempts=30
    local attempt=1
    
    log "INFO" "Waiting for services to be healthy..."
    
    while [[ $attempt -le $max_attempts ]]; do
        local healthy_count=$(docker-compose ps -q | xargs docker inspect --format='{{.State.Health.Status}}' 2>/dev/null | grep -c "healthy" || echo "0")
        local total_services=$(docker-compose ps -q | wc -l)
        
        if [[ $healthy_count -eq $total_services ]] && [[ $total_services -gt 0 ]]; then
            log "INFO" "All services are healthy"
            return 0
        fi
        
        log "INFO" "Health check $attempt/$max_attempts: $healthy_count/$total_services services healthy"
        sleep 10
        ((attempt++))
    done
    
    log "WARN" "Some services may not be fully healthy. Check 'docker-compose ps' for details"
}

create_backup() {
    local backup_name="teder-backup-$(date +%Y%m%d-%H%M%S)"
    local backup_dir="backups/$backup_name"
    
    log "INFO" "Creating backup: $backup_name"
    
    mkdir -p "$backup_dir"
    
    # Backup configuration and logs
    cp -r config "$backup_dir/" 2>/dev/null || log "WARN" "No config directory to backup"
    cp -r logs "$backup_dir/" 2>/dev/null || log "WARN" "No logs directory to backup"
    cp .env "$backup_dir/" 2>/dev/null || log "WARN" "No .env file to backup"
    
    # Backup volumes
    if docker volume ls | grep -q teder; then
        docker run --rm \
            -v teder_redis-data:/source:ro \
            -v "$PWD/$backup_dir":/backup \
            alpine tar czf /backup/redis-data.tar.gz -C /source .
    fi
    
    # Create manifest
    cat > "$backup_dir/manifest.txt" << EOF
Backup created: $(date)
Git commit: $(git rev-parse HEAD 2>/dev/null || echo "unknown")
Docker images: 
$(docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}" | grep teder || echo "none")
EOF
    
    # Compress backup
    tar czf "$backup_dir.tar.gz" -C backups "$backup_name"
    rm -rf "$backup_dir"
    
    log "INFO" "Backup created: $backup_dir.tar.gz"
}

show_status() {
    log "INFO" "Service Status:"
    docker-compose ps
    
    echo
    log "INFO" "System Resources:"
    docker system df
    
    echo
    log "INFO" "Container Stats:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

show_logs() {
    local service="${1:-}"
    local follow="${2:-false}"
    
    if [[ -n "$service" ]]; then
        if [[ "$follow" == "true" ]]; then
            docker-compose logs -f "$service"
        else
            docker-compose logs --tail=100 "$service"
        fi
    else
        if [[ "$follow" == "true" ]]; then
            docker-compose logs -f
        else
            docker-compose logs --tail=100
        fi
    fi
}

cleanup_docker() {
    log "INFO" "Cleaning up Docker resources..."
    
    # Remove unused containers, networks, images, and volumes
    docker system prune -af --volumes
    
    log "INFO" "Docker cleanup completed"
}

# =================================================================
# Script Entry Point
# =================================================================

main() {
    local env="$DEFAULT_ENV"
    local force=false
    local verbose=false
    local command=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--env)
                env="$2"
                shift 2
                ;;
            -f|--force)
                force=true
                shift
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            setup|build|deploy|start|stop|restart|status|logs|backup|restore|cleanup|update)
                command="$1"
                shift
                break
                ;;
            *)
                log "ERROR" "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    if [[ -z "$command" ]]; then
        log "ERROR" "No command specified"
        show_usage
        exit 1
    fi
    
    # Set verbose mode
    if [[ "$verbose" == "true" ]]; then
        set -x
    fi
    
    log "INFO" "Starting $command for environment: $env"
    log "INFO" "Logging to: $LOG_FILE"
    
    cd "$SCRIPT_DIR"
    
    # Execute command
    case "$command" in
        setup)
            setup_vps
            ;;
        build)
            build_images
            ;;
        deploy)
            if [[ "$force" == "false" ]]; then
                read -p "Deploy to $env? [y/N] " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    log "INFO" "Deployment cancelled"
                    exit 0
                fi
            fi
            deploy_services
            ;;
        start)
            docker-compose start
            log "INFO" "Services started"
            ;;
        stop)
            docker-compose stop
            log "INFO" "Services stopped"
            ;;
        restart)
            docker-compose restart
            log "INFO" "Services restarted"
            ;;
        status)
            show_status
            ;;
        logs)
            local service="${1:-}"
            local follow=false
            if [[ "$service" == "--follow" ]] || [[ "$1" == "-f" ]]; then
                follow=true
                service=""
            fi
            show_logs "$service" "$follow"
            ;;
        backup)
            create_backup
            ;;
        cleanup)
            cleanup_docker
            ;;
        update)
            log "INFO" "Updating from git..."
            git pull
            deploy_services
            ;;
        *)
            log "ERROR" "Unknown command: $command"
            exit 1
            ;;
    esac
    
    log "INFO" "$command completed successfully"
}

# Run main function with all arguments
main "$@"