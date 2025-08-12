#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone Package Builder for TederBot
Creates a fully self-contained distribution
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

class StandaloneBuilder:
    def __init__(self):
        self.root_dir = Path.cwd()
        self.dist_dir = self.root_dir / "standalone_dist"
        self.version = "1.0.0"
        self.build_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def clean_dist(self):
        """Clean distribution directory"""
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        self.dist_dir.mkdir(parents=True)
        print(f"[OK] Created directory: {self.dist_dir}")
        
    def install_pyinstaller(self):
        """Install PyInstaller if not present"""
        try:
            import PyInstaller
            print("[OK] PyInstaller is installed")
        except ImportError:
            print("[INFO] Installing PyInstaller...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("[OK] PyInstaller installed")
            
    def create_standalone_script(self):
        """Create a standalone entry point"""
        standalone_content = '''#!/usr/bin/env python3
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
                print(f"Starting in {i}...", end='\\r')
                time.sleep(1)
            print()
        
        print("[INFO] Starting trading bot...")
        print("Press Ctrl+C to stop")
        print()
        
        # Create and run bot
        bot = LiveTradingBot(dry_run=dry_run)
        bot.run()
        
    except KeyboardInterrupt:
        print("\\n[INFO] Bot stopped by user")
    except ImportError as e:
        print(f"[ERROR] Missing module: {e}")
        print("Please reinstall the program.")
        input("Press Enter to exit...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
'''
        
        script_path = self.dist_dir / "tederbot_main.py"
        script_path.write_text(standalone_content, encoding='utf-8')
        print("[OK] Created standalone script")
        return script_path
        
    def copy_source_files(self):
        """Copy all necessary source files"""
        # Files and directories to include
        items_to_copy = [
            "main_live.py",
            "src/",
            "config/",
            "backtest/",
            "requirements.txt"
        ]
        
        for item in items_to_copy:
            source = self.root_dir / item
            if source.exists():
                if source.is_dir():
                    dest = self.dist_dir / item
                    shutil.copytree(source, dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                    print(f"[OK] Copied directory: {item}")
                else:
                    shutil.copy2(source, self.dist_dir)
                    print(f"[OK] Copied file: {item}")
                    
    def create_spec_file(self, entry_script):
        """Create PyInstaller spec file"""
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{entry_script.name}'],
    pathex=['{self.dist_dir}'],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('config', 'config'),
        ('backtest', 'backtest'),
    ],
    hiddenimports=[
        'pandas',
        'numpy',
        'requests',
        'dotenv',
        'rich',
        'pandas_ta',
        'src.api.coinone_client',
        'src.indicators.rsi',
        'src.indicators.ema',
        'backtest.backtest_engine',
        'config.settings',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TederBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
'''
        spec_path = self.dist_dir / "tederbot.spec"
        spec_path.write_text(spec_content, encoding='utf-8')
        print("[OK] Created spec file")
        return spec_path
        
    def build_executable(self, spec_path):
        """Build executable with PyInstaller"""
        print("\n[INFO] Building executable with PyInstaller...")
        print("This may take a few minutes...")
        
        # Change to dist directory for build
        os.chdir(self.dist_dir)
        
        try:
            # Run PyInstaller with spec file (no additional options)
            result = subprocess.run([
                sys.executable, "-m", "PyInstaller",
                str(spec_path.name)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("[OK] Executable built successfully")
                
                # Find the executable
                exe_path = self.dist_dir / "dist" / "TederBot.exe"
                if exe_path.exists():
                    # Move to main dist directory
                    final_exe = self.dist_dir / "TederBot.exe"
                    shutil.move(exe_path, final_exe)
                    print(f"[OK] Executable location: {final_exe}")
                    
                    # Get file size
                    size_mb = final_exe.stat().st_size / (1024 * 1024)
                    print(f"[INFO] Executable size: {size_mb:.2f} MB")
                    
                    return final_exe
            else:
                print(f"[ERROR] Build failed: {result.stderr}")
                return None
                
        finally:
            # Return to original directory
            os.chdir(self.root_dir)
            
    def create_final_package(self, exe_path):
        """Create final distribution package"""
        # Create final package directory
        final_dir = self.root_dir / f"TederBot_Standalone_{self.version}"
        if final_dir.exists():
            shutil.rmtree(final_dir)
        final_dir.mkdir()
        
        # Copy executable
        if exe_path and exe_path.exists():
            shutil.copy2(exe_path, final_dir / "TederBot.exe")
        
        # Create batch runner
        batch_content = '''@echo off
echo ========================================
echo TederBot - USDT/KRW Auto Trading System
echo ========================================
echo.

TederBot.exe

pause
'''
        (final_dir / "Run_TederBot.bat").write_text(batch_content)
        
        # Create README
        readme_content = f'''TederBot v{self.version} - Standalone Edition

QUICK START:
1. Run "Run_TederBot.bat" or "TederBot.exe"
2. On first run, edit the created .env file with your API keys
3. Run again to start trading

REQUIREMENTS:
- Windows 10 or later
- Internet connection
- Coinone API keys

SUPPORT:
Build: {self.build_time}
'''
        (final_dir / "README.txt").write_text(readme_content)
        
        print(f"\n[OK] Final package created: {final_dir}")
        return final_dir
        
    def build(self):
        """Run the complete build process"""
        print("="*50)
        print("TederBot Standalone Builder")
        print("="*50)
        print()
        
        try:
            # Clean and prepare
            self.clean_dist()
            
            # Install PyInstaller
            self.install_pyinstaller()
            
            # Copy source files
            self.copy_source_files()
            
            # Create standalone script
            entry_script = self.create_standalone_script()
            
            # Create spec file
            spec_path = self.create_spec_file(entry_script)
            
            # Build executable
            exe_path = self.build_executable(spec_path)
            
            if exe_path:
                # Create final package
                final_dir = self.create_final_package(exe_path)
                
                print("\n" + "="*50)
                print("BUILD SUCCESS!")
                print("="*50)
                print(f"\nStandalone package ready: {final_dir}")
                print("\nThe package contains a single .exe file that includes everything.")
                print("Users only need to:")
                print("1. Run TederBot.exe")
                print("2. Edit .env file on first run")
                print("3. Start trading!")
            else:
                print("\n[ERROR] Build failed. Check the errors above.")
                
        except Exception as e:
            print(f"\n[ERROR] Build failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    builder = StandaloneBuilder()
    builder.build()