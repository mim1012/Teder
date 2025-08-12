@echo off
chcp 65001 >nul
echo ========================================
echo USDT/KRW Market Price Check
echo ========================================
echo.

REM Simple Python check
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python is not installed.
        echo Please install Python from https://www.python.org/
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

REM Install requirements if needed
if not exist venv (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv venv
)

REM Activate venv and run
call venv\Scripts\activate.bat
pip install requests >nul 2>&1
%PYTHON_CMD% check_market.py

pause