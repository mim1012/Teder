@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo TederBot Installation
echo ========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python first:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" option!
    pause
    exit /b 1
)

echo Python detected.
echo Installing required packages...
echo.

pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ========================================
echo Installation completed!
echo.
echo Next steps:
echo 1. Copy .env.example to .env
echo 2. Enter API keys in .env file
echo 3. Run run_test.bat for paper trading test
echo ========================================
pause