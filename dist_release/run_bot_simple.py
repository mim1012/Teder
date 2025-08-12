#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified TederBot Runner for Distribution
"""

import sys
import os
import time
from pathlib import Path

def setup_environment():
    """Setup Python path and environment"""
    # Get the directory of this script
    script_dir = Path(__file__).parent.absolute()
    
    # Add bot directory to Python path
    bot_dir = script_dir / 'bot'
    if bot_dir.exists():
        sys.path.insert(0, str(bot_dir))
        print(f"[INFO] Added to path: {bot_dir}")
    
    # Change to script directory
    os.chdir(script_dir)
    print(f"[INFO] Working directory: {os.getcwd()}")
    
    # Create logs directory
    logs_dir = script_dir / 'logs'
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True)
        print(f"[INFO] Created logs directory")
    
    return script_dir, bot_dir

def check_environment():
    """Check if environment is properly set up"""
    # Check for .env file
    if not Path('.env').exists():
        print("[WARNING] .env file not found!")
        print("Please copy .env.example to .env and add your API keys.")
        
        # Check if .env.example exists
        if Path('.env.example').exists():
            print("\nCreating .env from template...")
            import shutil
            shutil.copy('.env.example', '.env')
            print("[INFO] Created .env file. Please edit it with your API keys.")
            return False
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("[INFO] Environment variables loaded")
        return True
    except ImportError:
        print("[WARNING] python-dotenv not installed")
        return True

def run_bot():
    """Run the trading bot"""
    try:
        print("\n" + "="*50)
        print("Starting TederBot...")
        print("="*50)
        
        # Try to import and run main_live
        import main_live
        
        if hasattr(main_live, 'main'):
            print("[INFO] Running main_live.main()")
            main_live.main()
        else:
            print("[INFO] Creating LiveTradingBot instance")
            from main_live import LiveTradingBot
            import os
            
            # Get DRY_RUN setting
            dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
            
            if dry_run:
                print("[INFO] Running in DRY_RUN mode (paper trading)")
            else:
                print("[WARNING] Running in LIVE mode (real money)")
                print("Waiting 5 seconds... Press Ctrl+C to cancel")
                time.sleep(5)
            
            # Create and run bot
            bot = LiveTradingBot(dry_run=dry_run)
            bot.run()
            
    except ImportError as e:
        print(f"\n[ERROR] Import failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure all required packages are installed (run install.bat)")
        print("2. Check if all .pyc files are present in the bot/ directory")
        print(f"3. Current Python path: {sys.path}")
        
        # Try to show what's missing
        import traceback
        traceback.print_exc()
        
    except KeyboardInterrupt:
        print("\n[INFO] Bot stopped by user")
        
    except Exception as e:
        print(f"\n[ERROR] Runtime error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main entry point"""
    print("TederBot Distribution Package")
    print(f"Python version: {sys.version}")
    print(f"Script location: {__file__}")
    print()
    
    # Setup environment
    script_dir, bot_dir = setup_environment()
    
    # Check environment
    env_ok = check_environment()
    
    if not env_ok:
        print("\n[ERROR] Please configure .env file and restart")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Run the bot
    run_bot()
    
    print("\n[INFO] Bot terminated")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()