#!/bin/bash

# =================================================================
# Firewall Setup Script for Teder Trading Bot VPS
# =================================================================

set -euo pipefail

readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

log() {
    local level="$1"
    shift
    local message="$*"
    
    case "$level" in
        "INFO")  echo -e "${GREEN}[INFO]${NC} $message" ;;
        "WARN")  echo -e "${YELLOW}[WARN]${NC} $message" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $message" ;;
    esac
}

setup_ufw() {
    log "INFO" "Setting up UFW firewall..."
    
    # Reset UFW to defaults
    sudo ufw --force reset
    
    # Set default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH (modify port if using custom SSH port)
    log "INFO" "Allowing SSH access..."
    sudo ufw allow ssh
    # sudo ufw allow 2222/tcp  # Uncomment if using custom SSH port
    
    # Allow HTTP/HTTPS for monitoring dashboards (optional)
    log "INFO" "Allowing HTTP/HTTPS for monitoring..."
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Allow monitoring ports (restrict to specific IPs in production)
    log "INFO" "Allowing monitoring ports..."
    sudo ufw allow 9100/tcp comment "Node Exporter"
    sudo ufw allow 9090/tcp comment "Prometheus"
    sudo ufw allow 3000/tcp comment "Grafana"
    
    # Allow Docker internal communication
    log "INFO" "Allowing Docker internal network..."
    sudo ufw allow from 172.17.0.0/16
    sudo ufw allow from 172.20.0.0/16
    
    # Block common attack ports
    log "INFO" "Blocking common attack ports..."
    sudo ufw deny 23/tcp comment "Telnet"
    sudo ufw deny 135/tcp comment "RPC"
    sudo ufw deny 139/tcp comment "NetBIOS"
    sudo ufw deny 445/tcp comment "SMB"
    sudo ufw deny 1433/tcp comment "MSSQL"
    sudo ufw deny 3389/tcp comment "RDP"
    
    # Rate limiting for SSH
    log "INFO" "Setting up rate limiting..."
    sudo ufw limit ssh/tcp
    
    # Enable logging
    sudo ufw logging on
    
    # Enable firewall
    log "INFO" "Enabling UFW..."
    sudo ufw --force enable
    
    log "INFO" "UFW firewall setup completed"
}

setup_fail2ban() {
    log "INFO" "Setting up Fail2Ban..."
    
    # Install fail2ban if not present
    if ! command -v fail2ban-server >/dev/null 2>&1; then
        log "INFO" "Installing Fail2Ban..."
        sudo apt-get update
        sudo apt-get install -y fail2ban
    fi
    
    # Create local jail configuration
    sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
# Ban time in seconds (1 hour)
bantime = 3600

# Find time window (10 minutes)
findtime = 600

# Maximum retry attempts
maxretry = 3

# Ignore local IPs
ignoreip = 127.0.0.1/8 ::1 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16

# Ban action
banaction = iptables-multiport
banaction_allports = iptables-allports

# Email notifications (configure as needed)
# mta = sendmail
# destemail = admin@yourdomain.com
# sender = fail2ban@yourdomain.com

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600

[sshd-ddos]
enabled = true
port = ssh
filter = sshd-ddos
logpath = /var/log/auth.log
maxretry = 2
bantime = 7200
findtime = 120

# Docker log monitoring
[docker-auth]
enabled = true
filter = docker-auth
logpath = /var/log/docker.log
maxretry = 3
bantime = 3600
findtime = 600

# Web server protection (if running web interface)
[nginx-http-auth]
enabled = false
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = false
port = http,https
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 3

# Protection against port scanners
[port-scan]
enabled = true
filter = port-scan
logpath = /var/log/syslog
maxretry = 1
bantime = 86400
findtime = 600
EOF

    # Create custom filter for Docker authentication
    sudo tee /etc/fail2ban/filter.d/docker-auth.conf << 'EOF'
[Definition]
failregex = ^.*authentication failure.*rhost=<HOST>.*$
            ^.*Failed password.*from <HOST>.*$
ignoreregex =
EOF

    # Create port scan filter
    sudo tee /etc/fail2ban/filter.d/port-scan.conf << 'EOF'
[Definition]
failregex = ^.*kernel:.*IN=.*SRC=<HOST>.*DPT=(1|7|9|11|15|70|79|80|109|110|143|443|993|995).*$
ignoreregex =
EOF

    # Start and enable fail2ban
    sudo systemctl enable fail2ban
    sudo systemctl restart fail2ban
    
    log "INFO" "Fail2Ban setup completed"
}

setup_iptables_rules() {
    log "INFO" "Setting up additional iptables rules..."
    
    # Create iptables rules file
    sudo tee /etc/iptables/rules.v4 << 'EOF'
*filter
:INPUT DROP [0:0]
:FORWARD DROP [0:0]
:OUTPUT ACCEPT [0:0]

# Allow loopback
-A INPUT -i lo -j ACCEPT

# Allow established connections
-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH
-A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP/HTTPS
-A INPUT -p tcp --dport 80 -j ACCEPT
-A INPUT -p tcp --dport 443 -j ACCEPT

# Allow monitoring ports
-A INPUT -p tcp --dport 9090 -j ACCEPT
-A INPUT -p tcp --dport 9100 -j ACCEPT
-A INPUT -p tcp --dport 3000 -j ACCEPT

# Allow Docker networks
-A INPUT -s 172.17.0.0/16 -j ACCEPT
-A INPUT -s 172.20.0.0/16 -j ACCEPT

# Rate limiting for SSH
-A INPUT -p tcp --dport 22 -m state --state NEW -m recent --set --name ssh_attack
-A INPUT -p tcp --dport 22 -m state --state NEW -m recent --update --seconds 60 --hitcount 4 --name ssh_attack -j DROP

# Drop invalid packets
-A INPUT -m state --state INVALID -j DROP

# Protection against common attacks
-A INPUT -p tcp --tcp-flags ALL NONE -j DROP
-A INPUT -p tcp --tcp-flags ALL ALL -j DROP
-A INPUT -p tcp --tcp-flags ALL FIN,URG,PSH -j DROP
-A INPUT -p tcp --tcp-flags ALL SYN,RST,ACK,FIN,URG -j DROP
-A INPUT -p tcp --tcp-flags SYN,RST SYN,RST -j DROP
-A INPUT -p tcp --tcp-flags SYN,FIN SYN,FIN -j DROP

# Allow ping (ICMP)
-A INPUT -p icmp --icmp-type echo-request -j ACCEPT

COMMIT
EOF

    # Install iptables-persistent to save rules
    if ! dpkg -l | grep -q iptables-persistent; then
        log "INFO" "Installing iptables-persistent..."
        echo iptables-persistent iptables-persistent/autosave_v4 boolean true | sudo debconf-set-selections
        echo iptables-persistent iptables-persistent/autosave_v6 boolean true | sudo debconf-set-selections
        sudo apt-get install -y iptables-persistent
    fi
    
    log "INFO" "iptables rules setup completed"
}

setup_network_security() {
    log "INFO" "Configuring network security settings..."
    
    # Create sysctl configuration for network security
    sudo tee /etc/sysctl.d/99-network-security.conf << 'EOF'
# IP Spoofing protection
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.rp_filter = 1

# Ignore ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

# Ignore send redirects
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Disable source packet routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Log Martians
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# Ignore ICMP ping requests
net.ipv4.icmp_echo_ignore_all = 0

# Ignore Directed pings
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Disable IPv6 if not needed
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1

# TCP SYN flood protection
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 5

# Connection tracking
net.netfilter.nf_conntrack_max = 65536
net.netfilter.nf_conntrack_tcp_timeout_established = 1800

# Buffer overflow protection
kernel.exec-shield = 1
kernel.randomize_va_space = 2
EOF

    # Apply sysctl settings
    sudo sysctl -p /etc/sysctl.d/99-network-security.conf
    
    log "INFO" "Network security settings applied"
}

create_security_monitoring() {
    log "INFO" "Setting up security monitoring..."
    
    # Create security monitoring script
    sudo tee /opt/teder/scripts/security-monitor.sh << 'EOF'
#!/bin/bash

# Security monitoring script
LOG_FILE="/var/log/security-monitor.log"

# Check for failed login attempts
FAILED_LOGINS=$(grep "Failed password" /var/log/auth.log | wc -l)
if [ $FAILED_LOGINS -gt 10 ]; then
    echo "$(date): High number of failed logins: $FAILED_LOGINS" >> $LOG_FILE
fi

# Check for root login attempts
ROOT_ATTEMPTS=$(grep "Failed password for root" /var/log/auth.log | wc -l)
if [ $ROOT_ATTEMPTS -gt 0 ]; then
    echo "$(date): Root login attempts detected: $ROOT_ATTEMPTS" >> $LOG_FILE
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): High disk usage: ${DISK_USAGE}%" >> $LOG_FILE
fi

# Check for listening ports
PORTS=$(netstat -tuln | grep LISTEN | wc -l)
echo "$(date): Listening ports: $PORTS" >> $LOG_FILE
EOF

    chmod +x /opt/teder/scripts/security-monitor.sh
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "*/15 * * * * /opt/teder/scripts/security-monitor.sh") | crontab -
    
    log "INFO" "Security monitoring script created"
}

show_status() {
    log "INFO" "Security Configuration Status:"
    echo
    
    # UFW status
    echo "UFW Status:"
    sudo ufw status verbose
    echo
    
    # Fail2Ban status
    echo "Fail2Ban Status:"
    sudo fail2ban-client status
    echo
    
    # Listening ports
    echo "Listening Ports:"
    ss -tuln
    echo
    
    # Active connections
    echo "Active Connections:"
    ss -tu state established
}

main() {
    local action="${1:-setup}"
    
    case "$action" in
        "setup")
            log "INFO" "Starting security setup..."
            setup_ufw
            setup_fail2ban
            setup_network_security
            create_security_monitoring
            log "INFO" "Security setup completed!"
            ;;
        "status")
            show_status
            ;;
        "help")
            echo "Usage: $0 [setup|status|help]"
            echo
            echo "Commands:"
            echo "  setup   - Configure firewall and security (default)"
            echo "  status  - Show current security status"
            echo "  help    - Show this help message"
            ;;
        *)
            log "ERROR" "Unknown command: $action"
            exit 1
            ;;
    esac
}

# Ensure script is run as root or with sudo
if [[ $EUID -ne 0 ]] && [[ $1 != "help" ]]; then
    log "ERROR" "This script must be run as root or with sudo"
    exit 1
fi

# Execute main function
main "$@"