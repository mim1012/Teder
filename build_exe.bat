@echo off
echo ================================================================================
echo                          TEDER BOT EXE 빌드 스크립트
echo ================================================================================
echo.

REM Python이 설치되어 있는지 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 오류: Python이 설치되지 않았거나 PATH에 등록되지 않았습니다.
    echo Python 3.8 이상을 설치하고 PATH에 등록해주세요.
    pause
    exit /b 1
)

REM pip 업그레이드
echo pip 업그레이드 중...
python -m pip install --upgrade pip

REM 필요한 패키지 설치
echo 필요한 패키지들을 설치합니다...
python -m pip install -r requirements_exe.txt

REM EXE 빌드 실행
echo.
echo EXE 파일을 빌드합니다...
python build_exe.py

echo.
echo 빌드가 완료되었습니다!
echo dist 폴더를 확인하세요.
pause