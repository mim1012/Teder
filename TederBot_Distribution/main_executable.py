#!/usr/bin/env python3
import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

def setup_logging():
    # Ensure logs directory exists
    if not Path('logs').exists():
        Path('logs').mkdir()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'logs/tederbot_{datetime.now().strftime("%Y%m%d")}.log')
        ]
    )
    return logging.getLogger(__name__)

class TederBot:
    def __init__(self):
        self.logger = setup_logging()
        self.running = False
        
    def load_env(self):
        env_files = ['.env', 'secrets.env']
        env_loaded = False
        
        for env_file in env_files:
            if Path(env_file).exists():
                self.logger.info(f"Loading environment from {env_file}")
                try:
                    with open(env_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                if '=' in line:
                                    key, value = line.split('=', 1)
                                    os.environ[key.strip()] = value.strip().strip('"')
                    env_loaded = True
                    break
                except Exception as e:
                    self.logger.error(f"Error loading {env_file}: {e}")
        
        if not env_loaded:
            self.logger.error("No .env file found!")
            self.logger.info("Please create a .env file with:")
            self.logger.info("  COINONE_ACCESS_TOKEN=YOUR_ACCESS_TOKEN")
            self.logger.info("  COINONE_SECRET_KEY=YOUR_SECRET_KEY")
            self.logger.info("  DRY_RUN=True")
            return False
        
        required_keys = ['COINONE_ACCESS_TOKEN', 'COINONE_SECRET_KEY']
        missing_keys = []
        for key in required_keys:
            if key not in os.environ or not os.environ[key]:
                missing_keys.append(key)
        
        if missing_keys:
            self.logger.error(f"Missing required environment variables: {', '.join(missing_keys)}")
            return False
        
        return True
    
    def run(self):
        self.logger.info("="*50)
        self.logger.info("TederBot - USDT/KRW Auto Trading System")
        self.logger.info("="*50)
        
        if not self.load_env():
            self.logger.error("Failed to load environment variables")
            input("\nPress Enter to exit...")
            return
        
        dry_run = os.environ.get('DRY_RUN', 'True').lower() == 'true'
        
        if dry_run:
            self.logger.info("Running in PAPER TRADING mode (DRY_RUN=True)")
        else:
            self.logger.warning("="*50)
            self.logger.warning("WARNING: LIVE TRADING MODE (REAL MONEY)")
            self.logger.warning("="*50)
            time.sleep(3)
        
        self.logger.info("Bot initialization complete")
        self.logger.info("Starting trading strategy...")
        
        try:
            self.running = True
            cycle = 0
            while self.running:
                cycle += 1
                self.logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Cycle #{cycle}")
                self.logger.info("Checking market conditions...")
                
                # Trading logic would go here
                # For now, just simulate running
                
                time.sleep(10)  # Check every 10 seconds for testing
                
                if cycle >= 3:  # Stop after 3 cycles for testing
                    self.logger.info("Test completed - stopping bot")
                    break
                
        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        finally:
            self.running = False
            self.logger.info("Bot shutdown complete")

def main():
    try:
        bot = TederBot()
        bot.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()