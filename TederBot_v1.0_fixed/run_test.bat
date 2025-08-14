@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo TederBot - Test Mode (Paper Trading)
echo ========================================
echo.

if not exist ".env" (
    echo [ERROR] .env file not found!
    echo.
    echo 1. Copy .env.example to .env
    echo 2. Enter your Coinone API keys
    pause
    exit /b 1
)

if not exist "logs" mkdir logs

echo Starting in test mode...
echo No real money will be used.
echo.
echo To stop: Press Ctrl+C
echo ========================================
echo.

python main_live.py

echo.
echo Program terminated.
pause