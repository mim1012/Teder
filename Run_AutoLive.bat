@echo off
chcp 65001 >nul 2>&1
setlocal EnableExtensions EnableDelayedExpansion

echo ========================================
echo TederBot - USDT/KRW Auto Trading (LIVE)
echo ========================================
echo.

cd /d "%~dp0"

rem Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

rem Check for .env file
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Please create .env file with your API keys:
    echo   COINONE_ACCESS_TOKEN=your_token
    echo   COINONE_SECRET_KEY=your_secret
    echo   DRY_RUN=False
    pause
    exit /b 1
)

rem Install required packages if needed
echo Checking dependencies...
python -c "import pandas" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing required packages...
    pip install -r requirements.txt
)

rem Create logs directory if it doesn't exist
if not exist logs mkdir logs

rem Run the actual trading bot
echo.
echo Starting TederBot with main_live.py...
echo ========================================
echo.

python main_live.py

echo.
echo ========================================
echo Program terminated.
pause
exit /b 0