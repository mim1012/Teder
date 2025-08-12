@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo USDT/KRW Auto Trading Bot - LIVE TRADING
echo ========================================
echo.
echo !!! WARNING !!!
echo This will execute REAL trades with REAL money.
echo Make sure to test with small amounts first.
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
    echo Please create .env file with your API keys.
    echo.
    pause
    exit /b 1
)

REM Check DRY_RUN setting
findstr /C:"DRY_RUN=False" .env >nul
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Currently in PAPER TRADING mode.
    echo To enable LIVE trading, set DRY_RUN=False in .env
    echo.
    set /p continue="Continue in paper trading mode? (Y/N): "
    if /i not "%continue%"=="Y" (
        exit /b 0
    )
)

REM Create logs directory
if not exist logs (
    mkdir logs
)

echo.
echo Starting LIVE TRADING mode...
echo Press Ctrl+C to stop
echo ========================================
echo.

REM Final confirmation
echo ARE YOU SURE YOU WANT TO START LIVE TRADING?
echo Starting in 10 seconds...
timeout /t 10

REM Run main program
python main.py

echo.
echo Program terminated.
pause