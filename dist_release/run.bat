@echo off
chcp 65001 >nul 2>&1
echo ================================
echo TederBot 실행
echo ================================
echo.

REM .env 파일 확인
if not exist .env (
    echo [오류] .env 파일이 없습니다!
    echo .env.example을 .env로 복사하고 API 키를 입력하세요.
    pause
    exit /b 1
)

REM 가상환경 활성화
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo [오류] 가상환경이 없습니다. install.bat을 먼저 실행하세요.
    pause
    exit /b 1
)

REM 현재 디렉토리 확인
echo Current directory: %cd%
echo.

REM 봇 실행
echo Starting TederBot...
echo Press Ctrl+C to stop.
echo.
python run_bot.py

pause
