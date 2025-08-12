#!/bin/bash
# =============================================================================
# TEDER Trading Bot 모니터링 설정 스크립트
# =============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MONITORING_DIR="$PROJECT_DIR/monitoring"

# 로그 함수
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 모니터링 디렉토리 생성
create_monitoring_dirs() {
    log_info "모니터링 디렉토리를 생성합니다..."
    
    mkdir -p "$MONITORING_DIR/prometheus"
    mkdir -p "$MONITORING_DIR/grafana/dashboards"
    mkdir -p "$MONITORING_DIR/grafana/datasources"
    mkdir -p "$MONITORING_DIR/fluentd"
    mkdir -p "$MONITORING_DIR/alertmanager"
}

# Prometheus 설정
setup_prometheus() {
    log_info "Prometheus 설정을 생성합니다..."
    
    cat > "$MONITORING_DIR/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'teder-trading-bot'

rule_files:
  - "/etc/prometheus/rules/*.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'teder-trading-bot'
    static_configs:
      - targets: ['teder-trading-bot:9100']
    scrape_interval: 30s
    metrics_path: '/metrics'
    scrape_timeout: 10s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    metrics_path: '/metrics'

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['host.docker.internal:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - 'alertmanager:9093'
EOF

    # 알림 규칙 생성
    mkdir -p "$MONITORING_DIR/prometheus/rules"
    cat > "$MONITORING_DIR/prometheus/rules/trading-alerts.yml" << 'EOF'
groups:
  - name: trading_bot_alerts
    rules:
      - alert: TradingBotDown
        expr: up{job="teder-trading-bot"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Trading Bot is down"
          description: "The trading bot has been down for more than 1 minute."

      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 90% for more than 5 minutes."

      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is above 80% for more than 5 minutes."

      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space"
          description: "Disk space is below 10%."

      - alert: TradingErrorRate
        expr: rate(trading_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High trading error rate"
          description: "Trading error rate is above 10% for more than 2 minutes."
EOF
}

# Grafana 설정
setup_grafana() {
    log_info "Grafana 설정을 생성합니다..."
    
    # 데이터소스 설정
    cat > "$MONITORING_DIR/grafana/datasources/prometheus.yml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: "15s"
      queryTimeout: "60s"
      httpMethod: "POST"
EOF

    # 대시보드 프로비저닝 설정
    cat > "$MONITORING_DIR/grafana/dashboards/dashboard.yml" << 'EOF'
apiVersion: 1

providers:
  - name: 'TEDER Trading Bot'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

    # 거래 봇 대시보드 생성
    cat > "$MONITORING_DIR/grafana/dashboards/trading-bot-dashboard.json" << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "TEDER Trading Bot Dashboard",
    "tags": ["trading", "cryptocurrency", "coinone"],
    "style": "dark",
    "timezone": "Asia/Seoul",
    "panels": [
      {
        "id": 1,
        "title": "Trading Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"teder-trading-bot\"}",
            "legendFormat": "Bot Status"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              {
                "options": {
                  "0": {
                    "text": "DOWN"
                  },
                  "1": {
                    "text": "UP"
                  }
                },
                "type": "value"
              }
            ],
            "thresholds": {
              "steps": [
                {
                  "color": "red",
                  "value": 0
                },
                {
                  "color": "green",
                  "value": 1
                }
              ]
            }
          }
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 0
        }
      },
      {
        "id": 2,
        "title": "Total Trades",
        "type": "stat",
        "targets": [
          {
            "expr": "trading_total_trades",
            "legendFormat": "Total Trades"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 0
        }
      },
      {
        "id": 3,
        "title": "Current Balance (KRW)",
        "type": "stat",
        "targets": [
          {
            "expr": "trading_balance_krw",
            "legendFormat": "KRW Balance"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "short",
            "decimals": 0
          }
        },
        "gridPos": {
          "h": 8,
          "w": 6,
          "x": 0,
          "y": 8
        }
      },
      {
        "id": 4,
        "title": "Current Balance (USDT)",
        "type": "stat",
        "targets": [
          {
            "expr": "trading_balance_usdt",
            "legendFormat": "USDT Balance"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "short",
            "decimals": 8
          }
        },
        "gridPos": {
          "h": 8,
          "w": 6,
          "x": 6,
          "y": 8
        }
      },
      {
        "id": 5,
        "title": "Win Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "trading_win_rate",
            "legendFormat": "Win Rate"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 0,
            "max": 100
          }
        },
        "gridPos": {
          "h": 8,
          "w": 6,
          "x": 12,
          "y": 8
        }
      },
      {
        "id": 6,
        "title": "Total P&L (KRW)",
        "type": "stat",
        "targets": [
          {
            "expr": "trading_total_pnl",
            "legendFormat": "Total P&L"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "short",
            "decimals": 0,
            "thresholds": {
              "steps": [
                {
                  "color": "red",
                  "value": null
                },
                {
                  "color": "green",
                  "value": 0
                }
              ]
            }
          }
        },
        "gridPos": {
          "h": 8,
          "w": 6,
          "x": 18,
          "y": 8
        }
      },
      {
        "id": 7,
        "title": "RSI Indicator",
        "type": "timeseries",
        "targets": [
          {
            "expr": "trading_rsi_value",
            "legendFormat": "RSI"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 100,
            "thresholds": {
              "steps": [
                {
                  "color": "green",
                  "value": 0
                },
                {
                  "color": "yellow",
                  "value": 30
                },
                {
                  "color": "red",
                  "value": 70
                }
              ]
            }
          }
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 16
        }
      },
      {
        "id": 8,
        "title": "EMA Indicator",
        "type": "timeseries",
        "targets": [
          {
            "expr": "trading_ema_value",
            "legendFormat": "EMA(20)"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 16
        }
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
EOF
}

# Alertmanager 설정
setup_alertmanager() {
    log_info "Alertmanager 설정을 생성합니다..."
    
    cat > "$MONITORING_DIR/alertmanager/alertmanager.yml" << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alertmanager@teder-bot.local'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://127.0.0.1:5001/'
        send_resolved: true

  - name: 'email-notifications'
    email_configs:
      - to: 'admin@teder-bot.local'
        subject: 'TEDER Trading Bot Alert: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
EOF
}

# Fluentd 설정
setup_fluentd() {
    log_info "Fluentd 설정을 생성합니다..."
    
    cat > "$MONITORING_DIR/fluentd/fluent.conf" << 'EOF'
<source>
  @type tail
  path /var/log/teder/*.log
  pos_file /var/log/fluentd/teder.log.pos
  tag teder.trading
  <parse>
    @type json
    time_format %Y-%m-%d %H:%M:%S
    time_key timestamp
  </parse>
</source>

<source>
  @type tail
  path /var/log/teder/error.log
  pos_file /var/log/fluentd/teder.error.log.pos
  tag teder.error
  <parse>
    @type json
    time_format %Y-%m-%d %H:%M:%S
    time_key timestamp
  </parse>
</source>

<filter teder.**>
  @type grep
  <regexp>
    key level
    pattern (ERROR|CRITICAL|WARNING)
  </regexp>
</filter>

<match teder.trading>
  @type copy
  <store>
    @type file
    path /var/log/fluentd/teder-trading
    append true
    time_slice_format %Y%m%d
    time_slice_wait 10m
    time_format %Y%m%dT%H%M%S%z
    compress gzip
    <buffer time>
      timekey 1h
      timekey_wait 10m
      flush_mode interval
      flush_interval 30s
    </buffer>
  </store>
  <store>
    @type stdout
    <format>
      @type json
    </format>
  </store>
</match>

<match teder.error>
  @type copy
  <store>
    @type file
    path /var/log/fluentd/teder-error
    append true
    time_slice_format %Y%m%d
    time_slice_wait 10m
    time_format %Y%m%dT%H%M%S%z
    compress gzip
  </store>
  <store>
    @type webhook
    endpoint http://alertmanager:9093/api/v1/alerts
    <format>
      @type json
    </format>
  </store>
</match>
EOF
}

# 로그 회전 설정
setup_log_rotation() {
    log_info "로그 회전 설정을 생성합니다..."
    
    cat > "$MONITORING_DIR/logrotate.conf" << 'EOF'
/app/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 trader trader
    postrotate
        /usr/bin/docker kill -s SIGUSR1 $(docker ps -q --filter name=teder-trading-bot) || true
    endscript
}

/var/log/fluentd/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 fluentd fluentd
}
EOF
}

# 모니터링 스크립트 생성
create_monitoring_scripts() {
    log_info "모니터링 스크립트를 생성합니다..."
    
    # 시스템 모니터링 스크립트
    cat > "$MONITORING_DIR/system-monitor.sh" << 'EOF'
#!/bin/bash
# 시스템 모니터링 스크립트

LOGFILE="/app/logs/system-monitor.log"

log_metric() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOGFILE"
}

# CPU 사용률
cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
log_metric "CPU_USAGE:$cpu_usage"

# 메모리 사용률
mem_usage=$(free | grep Mem | awk '{printf("%.2f", $3/$2 * 100.0)}')
log_metric "MEMORY_USAGE:$mem_usage"

# 디스크 사용률
disk_usage=$(df -h /app | awk 'NR==2 {print $5}' | sed 's/%//')
log_metric "DISK_USAGE:$disk_usage"

# Docker 컨테이너 상태
container_status=$(docker inspect teder-trading-bot --format='{{.State.Status}}' 2>/dev/null || echo "not_found")
log_metric "CONTAINER_STATUS:$container_status"

# 네트워크 연결 테스트
if curl -s --connect-timeout 5 https://api.coinone.co.kr/v2/ticker/?currency=usdt >/dev/null; then
    log_metric "API_CONNECTION:ok"
else
    log_metric "API_CONNECTION:failed"
fi
EOF

    chmod +x "$MONITORING_DIR/system-monitor.sh"
    
    # 알림 테스트 스크립트
    cat > "$MONITORING_DIR/test-alerts.sh" << 'EOF'
#!/bin/bash
# 알림 테스트 스크립트

echo "Testing Prometheus alerts..."

# 테스트 메트릭 전송
cat << 'METRICS' | curl -X POST --data-binary @- http://localhost:9091/metrics/job/test
# HELP test_metric Test metric for alerting
# TYPE test_metric gauge
test_metric{instance="test"} 1
METRICS

echo "Test alert sent to Prometheus pushgateway"
echo "Check Grafana dashboard and Alertmanager for alerts"
EOF

    chmod +x "$MONITORING_DIR/test-alerts.sh"
}

# 메인 실행 함수
main() {
    log_info "TEDER Trading Bot 모니터링 설정을 시작합니다..."
    
    create_monitoring_dirs
    setup_prometheus
    setup_grafana
    setup_alertmanager
    setup_fluentd
    setup_log_rotation
    create_monitoring_scripts
    
    log_info "모니터링 설정이 완료되었습니다!"
    log_info "다음 명령으로 모니터링 스택을 시작할 수 있습니다:"
    log_info "  docker-compose up -d prometheus grafana alertmanager"
    log_info ""
    log_info "접속 정보:"
    log_info "  - Grafana: http://localhost:3000 (admin/admin123)"
    log_info "  - Prometheus: http://localhost:9090"
    log_info "  - Alertmanager: http://localhost:9093"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi