@echo off
echo ======================================
echo COINONE SPLIT BUY STRATEGY BOT
echo ======================================
echo.

REM 가상환경 활성화 (있는 경우)
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Python 경로 확인
python --version
if %errorlevel% neq 0 (
    echo Error: Python not found
    pause
    exit /b 1
)

REM 필요한 패키지 설치 확인
echo Checking required packages...
python -c "import pandas, pandas_ta, rich" 2>nul
if %errorlevel% neq 0 (
    echo Installing required packages...
    pip install pandas pandas-ta rich requests
)

REM API 키 파일 확인
if not exist config\api_keys.py (
    echo.
    echo ERROR: config\api_keys.py not found!
    echo Please create this file with your Coinone API keys:
    echo.
    echo API_KEY = 'your_api_key_here'
    echo SECRET_KEY = 'your_secret_key_here'
    echo.
    pause
    exit /b 1
)

echo.
echo Starting Split Buy Strategy Bot...
echo Press Ctrl+C to stop the bot
echo.

REM 메인 스크립트 실행
python main_split_strategy.py

if %errorlevel% neq 0 (
    echo.
    echo Bot exited with error code: %errorlevel%
    pause
)

echo.
echo Bot stopped.
pause