@echo off
echo ========================================
echo USDT/KRW 자동매매 프로그램 - 실거래 모드
echo ========================================
echo.
echo !!! 경고 !!!
echo 이 프로그램은 실제 자금으로 거래를 실행합니다.
echo 반드시 소액으로 테스트 후 사용하세요.
echo ========================================
echo.

REM Python 경로 확인
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python이 설치되어 있지 않습니다.
    echo Python 3.8 이상을 설치해주세요.
    pause
    exit /b 1
)

REM 가상환경 확인 및 활성화
if exist venv\Scripts\activate.bat (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else (
    echo 가상환경이 없습니다. 생성 중...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo 필요한 패키지 설치 중...
    pip install -r requirements.txt
)

REM .env 파일 확인
if not exist .env (
    echo.
    echo [경고] .env 파일이 없습니다!
    echo .env.example을 .env로 복사하고 API 키를 입력하세요.
    echo.
    echo 1. .env.example을 .env로 복사
    echo 2. COINONE_ACCESS_TOKEN에 액세스 토큰 입력
    echo 3. COINONE_SECRET_KEY에 시크릿 키 입력
    echo 4. DRY_RUN=False로 변경 (실거래)
    echo.
    pause
    exit /b 1
)

REM .env에서 DRY_RUN 값 확인
findstr /C:"DRY_RUN=False" .env >nul
if %errorlevel% neq 0 (
    echo.
    echo [경고] 현재 모의거래 모드입니다.
    echo 실거래를 원하시면 .env 파일의 DRY_RUN=False로 변경하세요.
    echo.
    set /p continue="모의거래로 계속하시겠습니까? (Y/N): "
    if /i not "%continue%"=="Y" (
        exit /b 0
    )
)

REM logs 디렉토리 생성
if not exist logs (
    mkdir logs
)

echo.
echo 실거래 모드로 시작합니다...
echo 종료하려면 Ctrl+C를 누르세요.
echo ========================================
echo.

REM 실거래 확인
echo 정말로 실거래를 시작하시겠습니까?
echo 10초 후 자동으로 시작됩니다...
timeout /t 10

REM 메인 프로그램 실행
python main.py

echo.
echo 프로그램이 종료되었습니다.
pause