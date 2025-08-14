@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo TederBot - Live Trading Mode
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

echo ########################################
echo #  WARNING: LIVE TRADING (REAL MONEY)  #
echo ########################################
echo.
echo Make sure DRY_RUN=False in .env file
echo.
set /p confirm="Start live trading? (yes/no): "
if /i not "%confirm%"=="yes" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo Starting live trading...
echo To stop: Press Ctrl+C
echo ========================================
echo.

python main_live.py

echo.
echo Program terminated.
pause