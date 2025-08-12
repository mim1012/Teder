@echo off
chcp 65001 >nul 2>&1
setlocal EnableExtensions EnableDelayedExpansion

rem Change working directory to the script directory
cd /d "%~dp0"

echo ========================================
echo TederBot - USDT/KRW Auto Trading (LIVE)
echo ========================================
echo.

rem Preferred env file names in current directory
set "ENV_CANDIDATE1=%cd%\.env"
set "ENV_CANDIDATE2=%cd%\secrets.env"

rem Optional fallback (developer machine path)
set "ENV_FALLBACK=D:\Project\Teder\.env"

set "ENV_FILE="
if exist "%ENV_CANDIDATE1%" set "ENV_FILE=%ENV_CANDIDATE1%"
if not defined ENV_FILE if exist "%ENV_CANDIDATE2%" set "ENV_FILE=%ENV_CANDIDATE2%"
if not defined ENV_FILE if exist "%ENV_FALLBACK%" set "ENV_FILE=%ENV_FALLBACK%"

if not defined ENV_FILE (
    echo [ERROR] .env / secrets.env 파일을 찾을 수 없습니다.
    echo 현재 폴더에 .env 또는 secrets.env를 두거나 ENV_FALLBACK 경로를 수정하세요.
    echo.
    echo 예시 (.env):
    echo   COINONE_ACCESS_TOKEN=YOUR_ACCESS_TOKEN
    echo   COINONE_SECRET_KEY=YOUR_SECRET_KEY
    echo   DRY_RUN=False
    echo.
    pause
    exit /b 1
)

echo Using env file: %ENV_FILE%

rem Load key=value pairs from env file (skip comments and blanks)
for /f "usebackq tokens=1* delims== eol=#" %%A in (`type "%ENV_FILE%" ^| findstr /r /v "^[#;]" ^| findstr /r /v "^$"`) do (
    set "key=%%A"
    set "val=%%B"
    rem Trim possible quotes around value
    if defined val (
        if "!val:~0,1!"=="\"" set "val=!val:~1!"
        if "!val:~-1!"=="\"" set "val=!val:~0,-1!"
        set "!key!=!val!"
    )
)

rem Force LIVE trading mode unless explicitly overridden in env file
if /i "!DRY_RUN!"=="" set "DRY_RUN=False"

if /i "!DRY_RUN!"=="False" (
    echo.
    echo ========================================
    echo WARNING: LIVE TRADING MODE (REAL MONEY)
    echo ========================================
    echo.
) else (
    echo.
    echo Running in PAPER TRADING mode (DRY_RUN=True)
    echo.
)

rem Ensure logs directory exists
if not exist logs mkdir logs

rem Launch the bot executable
echo Starting TederBot.exe ...
"%cd%\TederBot.exe"

echo.
echo Program terminated.
endlocal
exit /b 0


