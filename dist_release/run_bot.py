#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TederBot Runner - Auto Trading Bot Runner"""

import sys
import os

# Add bot directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
bot_dir = os.path.join(script_dir, 'bot')
sys.path.insert(0, bot_dir)

# Set working directory
os.chdir(script_dir)

def main():
    try:
        # Create logs directory if not exists
        if not os.path.exists('logs'):
            os.makedirs('logs')
            print("[INFO] Created logs directory")
            
        # Import compiled main module
        import main_live
        
        # Run main function
        if hasattr(main_live, 'main'):
            main_live.main()
        else:
            print("[ERROR] main() function not found in main_live module")
            sys.exit(1)
            
    except ImportError as e:
        print(f"[ERROR] Import failed: {e}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Bot directory: {bot_dir}")
        print(f"Directory contents: {os.listdir(bot_dir) if os.path.exists(bot_dir) else 'Not found'}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"[ERROR] File not found: {e}")
        print(f"Working directory: {os.getcwd()}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Runtime error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
