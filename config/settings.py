"""
코인원 자동매매 봇 설정 파일
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# API Settings
API_CONFIG = {
    'base_url': 'https://api.coinone.co.kr',
    'access_token': os.getenv('COINONE_ACCESS_TOKEN'),
    'secret_key': os.getenv('COINONE_SECRET_KEY'),
    'timeout': 30,
    'max_retries': 3,
    'retry_delay': 1  # seconds
}

# Trading Settings
TRADING_CONFIG = {
    'symbol': 'USDT',
    'currency': 'KRW',
    'timeframe': '1h',  # 1시간봉
    'partial_fill_wait_time': 600,  # 10분 (600초)
    'profit_target': 4,  # 익절 목표: +4원
    'position_timeout': 86400,  # 24시간 (86400초)
    'restart_delay': 3600,  # 전략 재시작 대기: 1시간
}

# Technical Indicators Settings
INDICATORS_CONFIG = {
    'rsi_period': 14,
    'ema_period': 20,
    'rsi_overbought': 70,
    'ema_slope_3_threshold': 0.3,
    'ema_slope_5_threshold': 0.2,
}

# Monitoring Settings
MONITORING_CONFIG = {
    'update_interval': 1,  # 화면 업데이트 주기 (초)
    'log_level': 'INFO',
    'log_file': 'logs/trading_bot.log',
    'max_log_size': '10MB',
    'backup_count': 5,
}

# Backtest Settings
BACKTEST_CONFIG = {
    'start_date': None,  # Will be set dynamically
    'end_date': None,    # Will be set dynamically
    'initial_balance': 1000000,  # 초기 자금 100만원
    'limit_order_fee': 0.0000,   # 지정가 수수료 0%
    'market_order_fee': 0.0002,  # 시장가 수수료 0.02%
    'slippage': 0.0001,          # 슬리피지 0.01%
}

# System Settings
SYSTEM_CONFIG = {
    'timezone': 'Asia/Seoul',
    'debug_mode': os.getenv('DEBUG', 'False').lower() == 'true',
    'dry_run': os.getenv('DRY_RUN', 'True').lower() == 'true',  # 기본값: 모의거래
}

# Safety Settings
SAFETY_CONFIG = {
    'max_order_amount': 10000000,  # 최대 주문 금액: 1000만원
    'daily_trade_limit': 50,       # 일일 거래 횟수 제한
    'emergency_stop': False,       # 긴급 정지 플래그
}