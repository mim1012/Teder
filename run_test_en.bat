@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo USDT/KRW Auto Trading Bot - Paper Trading
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
    echo [WARNING] .env file not found!
    echo Please copy .env.example to .env and add your API keys.
    echo.
    echo Steps:
    echo 1. Copy .env.example to .env
    echo 2. Add your COINONE_ACCESS_TOKEN
    echo 3. Add your COINONE_SECRET_KEY
    echo 4. Confirm DRY_RUN=True for paper trading
    echo.
    pause
    exit /b 1
)

REM Create logs directory
if not exist logs (
    mkdir logs
)

echo.
echo Starting in PAPER TRADING mode...
echo (For live trading, set DRY_RUN=False in .env)
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

REM Run main program
python main_simple.py

echo.
echo Program terminated.
pause