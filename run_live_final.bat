@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo USDT/KRW Auto Trading Bot - Live Trading
echo ========================================
echo.

REM Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed.
    echo Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check and activate virtual environment
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Creating...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing required packages...
    pip install -r requirements.txt
)

REM Check .env file
if not exist .env (
    echo.
    echo [ERROR] .env file not found!
    echo Please copy .env.example to .env and add your API keys.
    echo.
    pause
    exit /b 1
)

REM Create logs directory
if not exist logs (
    mkdir logs
)

REM Check DRY_RUN setting
findstr /C:"DRY_RUN=False" .env >nul
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo WARNING: LIVE TRADING MODE DETECTED!
    echo ========================================
    echo.
    echo This will use REAL MONEY for trading!
    echo Make sure you understand the risks.
    echo.
    echo Press Ctrl+C within 10 seconds to cancel...
    echo.
    timeout /t 10
) else (
    echo.
    echo Running in PAPER TRADING mode (DRY_RUN=True)
    echo To enable live trading, set DRY_RUN=False in .env
    echo.
)

echo.
echo Starting trading bot...
echo Press Ctrl+C to stop
echo ========================================
echo.

REM Run live trading bot
python main_live.py

echo.
echo Program terminated.
pause