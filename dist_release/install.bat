@echo off
chcp 65001 >nul 2>&1
echo ================================
echo TederBot 설치 프로그램
echo ================================
echo.

REM Python 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] Python이 설치되지 않았습니다.
    echo Python 3.8 이상을 설치해주세요.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python 확인 완료
echo.

REM 가상환경 생성
if not exist venv (
    echo 가상환경 생성 중...
    python -m venv venv
)

REM 가상환경 활성화
call venv\Scripts\activate.bat

REM 패키지 설치
echo 필요한 패키지 설치 중...
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo.
echo ================================
echo 설치 완료!
echo ================================
echo.
echo 다음 단계:
echo 1. .env.example을 .env로 복사
echo 2. .env 파일에 API 키 입력
echo 3. run.bat 실행
echo.
pause
