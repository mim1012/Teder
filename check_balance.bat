@echo off
chcp 65001 >nul
echo ========================================
echo Coinone Balance Check
echo ========================================
echo.

REM Try python, python3, and py commands
where python >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto python_found
)

where python3 >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    goto python_found
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    goto python_found
)

echo [ERROR] Python is not installed or not in PATH.
echo Please install Python 3.8 or higher.
pause
exit /b 1

:python_found
echo Using Python: %PYTHON_CMD%

REM Check virtual environment
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Creating...
    %PYTHON_CMD% -m venv venv
    call venv\Scripts\activate.bat
    echo Installing required packages...
    pip install python-dotenv requests pandas numpy
)

REM Check .env file
if not exist .env (
    echo [ERROR] .env file not found!
    echo Please copy .env.example to .env and add your API keys.
    pause
    exit /b 1
)

REM Run balance check script
%PYTHON_CMD% check_balance.py

pause