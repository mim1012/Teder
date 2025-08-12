@echo off
chcp 65001 >nul
echo ========================================
echo Coinone Balance Check
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

REM Check if .env exists
if not exist .env (
    echo [ERROR] .env file not found!
    echo.
    echo Creating .env from template...
    copy .env.example .env
    echo.
    echo Please edit .env file and add your API keys:
    echo   COINONE_ACCESS_TOKEN=your_access_token
    echo   COINONE_SECRET_KEY=your_secret_key
    echo.
    pause
    exit /b 1
)

REM Install requirements if needed
if not exist venv (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv venv
)

REM Activate venv and run
call venv\Scripts\activate.bat
pip install python-dotenv requests >nul 2>&1
%PYTHON_CMD% check_balance.py

pause