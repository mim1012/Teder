@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo TederBot Initial Setup
echo ========================================
echo.

rem .env 파일이 이미 있는지 확인
if exist ".env" (
    echo .env file already exists.
    set /p overwrite="Overwrite? (yes/no): "
    if /i not "!overwrite!"=="yes" (
        echo Keeping existing settings.
        goto :skip_env
    )
)

rem .env.example을 .env로 복사
copy ".env.example" ".env" >nul 2>&1
echo .env file created.
echo.
echo [IMPORTANT] Enter the following in .env file:
echo   - COINONE_ACCESS_TOKEN
echo   - COINONE_SECRET_KEY
echo.
notepad .env

:skip_env
echo.
echo Setup completed.
echo.
echo Next steps:
echo 1. Run install.bat (install packages)
echo 2. Run run_test.bat (test with paper trading)
echo.
pause