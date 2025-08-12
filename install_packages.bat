@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo Installing Required Packages
echo ========================================
echo.

REM Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Python is not installed.
        echo Please install Python 3.8 or higher.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

REM Create virtual environment if not exists
if not exist venv (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install packages
echo.
echo Installing required packages...
pip install pandas numpy requests python-dotenv
pip install pandas-ta loguru rich
pip install matplotlib seaborn
pip install python-dateutil pytz

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Testing imports...
python -c "import pandas; import numpy; import requests; print('Core packages: OK')"
python -c "import pandas_ta; print('pandas-ta: OK')"
python -c "import loguru; import rich; print('Logging/UI: OK')"

echo.
pause