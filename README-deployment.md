# Teder Crypto Trading Bot - Production Deployment Guide

Complete guide for deploying the USDT/KRW automated trading bot on a production VPS server with Docker containerization.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Environment                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Trading Bot │  │Log Rotator  │  │ Monitoring  │         │
│  │ Container   │  │ Container   │  │ Container   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                 │
│  ┌──────┴──────────┬─────┴─────────┬──────┴──────┐         │
│  │     Volumes     │     Logs      │   Metrics   │         │
│  │   ./data/       │   ./logs/     │   :9100     │         │
│  │   ./config/     │               │             │         │
│  └─────────────────┴───────────────┴─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04/22.04 LTS or CentOS 8+
- **RAM**: Minimum 2GB, Recommended 4GB
- **Storage**: Minimum 20GB available space
- **Network**: Stable internet connection with low latency to Coinone API

### Software Dependencies
- Docker 24.0+ and Docker Compose 2.0+
- Git
- curl
- Basic system utilities (installed by setup script)

## 🚀 Quick Start Deployment

### 1. Initial VPS Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/teder-trading-bot.git
cd teder-trading-bot

# Make deployment script executable
chmod +x deploy.sh

# Run initial VPS setup (includes Docker, firewall, security)
./deploy.sh setup
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (REQUIRED)
nano .env
```

**Critical Environment Variables:**
```env
# Trading Configuration
DRY_RUN=false                    # Set to 'false' for live trading
COINONE_ACCESS_TOKEN=your_token  # Your Coinone API access token
COINONE_SECRET_KEY=your_secret   # Your Coinone API secret key

# Trading Parameters
PROFIT_TARGET=4                  # Profit target in KRW
MAX_HOLD_HOURS=24               # Maximum holding time
```

### 3. Deploy the Bot

```bash
# Deploy all services
./deploy.sh deploy

# Check deployment status
./deploy.sh status

# View logs
./deploy.sh logs --follow
```

## 🐳 Docker Configuration

### Multi-Stage Dockerfile
The `Dockerfile` uses multi-stage builds for optimal image size and security:

```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim as builder
# Install build dependencies and Python packages

# Stage 2: Production runtime
FROM python:3.11-slim as production
# Copy only runtime dependencies
# Run as non-root user 'teder'
# Health checks and monitoring
```

### Docker Compose Services

| Service | Description | Ports | Health Check |
|---------|-------------|-------|--------------|
| `teder-bot` | Main trading application | 8080 | API connectivity |
| `log-rotator` | Automatic log rotation | - | - |
| `monitoring` | System metrics (optional) | 9100 | Node exporter |
| `redis` | Caching layer (optional) | 6379 | Redis ping |

## 🔧 Configuration Management

### Environment Files
- `.env` - Main configuration (create from `.env.example`)
- `config/` - Additional configuration files
- `docker-compose.yml` - Service orchestration

### Key Configuration Options

#### Trading Settings
```env
DRY_RUN=true                    # Simulation mode
PROFIT_TARGET=4                 # Profit target in KRW
MAX_HOLD_HOURS=24              # Maximum hold time
RSI_PERIOD=14                  # RSI calculation period
EMA_PERIOD=20                  # EMA calculation period
```

#### Logging & Monitoring
```env
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR
LOG_RETENTION_DAYS=7           # Days to keep logs
MONITORING_ENABLED=true        # Enable metrics collection
```

#### Security
```env
API_RATE_LIMIT=100            # API calls per minute
MAX_CONNECTIONS=10            # Max concurrent connections
```

## 🔄 Auto-Restart & Health Checks

### Docker Health Checks
Built-in health check monitors:
- API connectivity to Coinone
- Container resource usage
- Application responsiveness

### Systemd Service (Optional)
```bash
# Install systemd service for auto-start on boot
sudo cp systemd/teder-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable teder-bot.service
```

### Health Monitoring Scripts
```bash
# Manual health check
./scripts/health-check.sh check

# Health check with auto-restart
./scripts/health-check.sh check true

# Force restart
./scripts/health-check.sh restart
```

## 📊 Logging & Monitoring

### Log Management
- **Location**: `./logs/`
- **Rotation**: Automatic via `log-rotator` service
- **Retention**: 7 days (configurable)
- **Compression**: Enabled for old logs

### Log Files
- `live_trading.log` - Trading activity and decisions
- `error.log` - Error messages and exceptions
- `access.log` - API call logs
- `debug.log` - Detailed debugging information

### Monitoring Stack (Optional)
Enable monitoring profile:
```bash
docker-compose --profile monitoring up -d
```

Access monitoring dashboards:
- **System Metrics**: http://your-server:9100/metrics
- **Prometheus**: http://your-server:9090 (if configured)
- **Grafana**: http://your-server:3000 (if configured)

## 🔐 Security Configuration

### Firewall Setup
```bash
# Configure firewall and security
./security/firewall-setup.sh setup

# Check security status
./security/firewall-setup.sh status
```

### Security Features
- **Non-root containers**: All containers run as unprivileged users
- **Network isolation**: Services communicate via dedicated Docker network
- **UFW firewall**: Configured with minimal required ports
- **Fail2Ban**: Protection against brute force attacks
- **Log monitoring**: Security event detection

### Open Ports (Firewall Rules)
- **SSH**: 22 (rate limited)
- **HTTP/HTTPS**: 80, 443 (for monitoring dashboards)
- **Monitoring**: 9100 (Node Exporter, optional)

## 🔄 Operations & Maintenance

### Daily Operations

#### Start/Stop Services
```bash
./deploy.sh start          # Start all services
./deploy.sh stop           # Stop all services  
./deploy.sh restart        # Restart all services
```

#### Log Management
```bash
./deploy.sh logs           # Show recent logs
./deploy.sh logs --follow  # Follow live logs
./deploy.sh logs teder-bot # Show specific service logs
```

#### System Status
```bash
./deploy.sh status         # Service and resource status
docker-compose ps          # Container status
docker stats              # Real-time container stats
```

### Backup & Recovery

#### Create Backup
```bash
./deploy.sh backup         # Create timestamped backup
```

Backup includes:
- Configuration files
- Log files
- Data volumes
- Environment settings

#### Update Deployment
```bash
git pull                   # Get latest code
./deploy.sh update         # Rebuild and restart
```

### Troubleshooting

#### Common Issues

1. **Container won't start**
   ```bash
   docker-compose logs teder-bot
   ./scripts/health-check.sh check
   ```

2. **API connection errors**
   - Verify Coinone API credentials
   - Check network connectivity
   - Review API rate limits

3. **High memory usage**
   ```bash
   docker stats
   ./deploy.sh cleanup  # Clean unused resources
   ```

4. **Log files growing too large**
   - Check log rotation configuration
   - Adjust `LOG_LEVEL` in `.env`
   - Manual log cleanup: `find ./logs -name "*.log" -mtime +7 -delete`

#### Debug Mode
```bash
# Enable debug logging
echo "LOG_LEVEL=DEBUG" >> .env
./deploy.sh restart

# View debug logs
./deploy.sh logs --follow | grep DEBUG
```

## ⚙️ Advanced Configuration

### Resource Limits
Modify `docker-compose.yml` to adjust resource allocation:
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

### Custom Networks
Configure custom Docker networks in `docker-compose.yml`:
```yaml
networks:
  teder-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Volume Management
Persistent data storage configuration:
```yaml
volumes:
  - ./logs:/app/logs:rw
  - ./data:/app/data:rw
  - ./config:/app/config:rw
```

## 📈 Performance Optimization

### System Tuning
```bash
# Optimize for trading applications
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'net.core.rmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Docker Optimization
- Use multi-stage builds to minimize image size
- Layer caching for faster builds
- Resource limits to prevent resource exhaustion
- Health checks for automatic recovery

## 🛡️ Production Checklist

Before going live with real trading:

- [ ] **API Credentials**: Valid Coinone API keys configured
- [ ] **Environment**: `DRY_RUN=false` for live trading
- [ ] **Security**: Firewall configured and tested
- [ ] **Monitoring**: Health checks and logging working
- [ ] **Backups**: Automatic backup system configured
- [ ] **Network**: Stable internet connection verified
- [ ] **Resources**: Sufficient CPU, RAM, and disk space
- [ ] **Testing**: Strategy tested with paper trading
- [ ] **Notifications**: Alert system configured (optional)

## 📞 Support & Maintenance

### Log Analysis
```bash
# Trading performance analysis
grep "BUY SIGNAL\|SELL ORDER" logs/live_trading.log | tail -20

# Error analysis  
grep "ERROR" logs/live_trading.log | tail -10

# API call analysis
grep "API" logs/live_trading.log | wc -l
```

### Performance Metrics
```bash
# Container resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# System resource usage
htop
df -h
iostat -x 1
```

### Emergency Procedures

#### Emergency Stop
```bash
./deploy.sh stop          # Stop trading immediately
docker-compose down        # Force stop all containers
```

#### Emergency Recovery
```bash
# Restore from backup
tar -xzf backups/teder-backup-YYYYMMDD-HHMMSS.tar.gz
./deploy.sh deploy --force
```

---

## 📝 Notes

- Always test configuration changes in a staging environment first
- Monitor system resources regularly to prevent issues
- Keep API credentials secure and rotate them periodically  
- Review trading logs daily for optimal performance
- Update the system and containers regularly for security

For additional support or advanced configurations, refer to the project documentation or contact the development team.