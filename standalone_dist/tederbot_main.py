#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TederBot Standalone Entry Point
All-in-one executable for distribution
"""

import os
import sys
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check and setup environment"""
    # Check for .env file
    if not Path('.env').exists():
        print("="*50)
        print("FIRST TIME SETUP")
        print("="*50)
        print()
        print("No .env file found. Creating from template...")
        
        # Create .env from embedded template
        env_template = """# TederBot Configuration
# Copy this file to .env and fill in your API credentials

# Coinone API Credentials
COINONE_ACCESS_TOKEN=your_access_token_here
COINONE_SECRET_KEY=your_secret_key_here

# Trading Mode
# true = Paper trading (no real money)
# false = Live trading (REAL MONEY - BE CAREFUL!)
DRY_RUN=true

# Trading Pair
TICKER=USDT
CURRENCY=KRW

# Optional: Telegram notifications
# TELEGRAM_BOT_TOKEN=
# TELEGRAM_CHAT_ID=
"""
        with open('.env', 'w') as f:
            f.write(env_template)
        
        print("[OK] Created .env file")
        print()
        print("IMPORTANT: Please edit .env file and add your Coinone API keys")
        print("Then restart the program.")
        print()
        input("Press Enter to exit...")
        sys.exit(0)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check API keys
    access_token = os.getenv('COINONE_ACCESS_TOKEN', '')
    secret_key = os.getenv('COINONE_SECRET_KEY', '')
    
    if 'your_' in access_token or 'your_' in secret_key or not access_token or not secret_key:
        print("[ERROR] API keys not configured!")
        print("Please edit .env file and add your Coinone API credentials.")
        input("Press Enter to exit...")
        sys.exit(1)
    
    return True

def main():
    """Main entry point"""
    print("="*50)
    print("TederBot - USDT/KRW Auto Trading System")
    print(f"Version: 1.0.0")
    print("="*50)
    print()
    
    try:
        # Check environment
        if not check_environment():
            return
        
        # Create logs directory
        if not os.path.exists('logs'):
            os.makedirs('logs')
            logger.info("Created logs directory")
        
        # Import and run the bot
        from main_live import LiveTradingBot
        
        # Get settings
        dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
        
        if dry_run:
            print("[INFO] Running in PAPER TRADING mode (no real money)")
        else:
            print("="*50)
            print("[WARNING] LIVE TRADING MODE - USING REAL MONEY!")
            print("="*50)
            print("The bot will start trading with real funds in 10 seconds.")
            print("Press Ctrl+C now to cancel...")
            print()
            for i in range(10, 0, -1):
                print(f"Starting in {i}...", end='\r')
                time.sleep(1)
            print()
        
        print("[INFO] Starting trading bot...")
        print("Press Ctrl+C to stop")
        print()
        
        # Create and run bot
        bot = LiveTradingBot(dry_run=dry_run)
        bot.run()
        
    except KeyboardInterrupt:
        print("\n[INFO] Bot stopped by user")
    except ImportError as e:
        print(f"[ERROR] Missing module: {e}")
        print("Please reinstall the program.")
        input("Press Enter to exit...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
