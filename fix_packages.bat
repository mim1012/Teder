@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo Fixing Package Dependencies
echo ========================================
echo.

REM Activate virtual environment
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found!
    pause
    exit /b 1
)

echo Installing setuptools for pkg_resources...
pip install --upgrade setuptools

echo.
echo Installing/Upgrading pandas-ta...
pip uninstall pandas-ta -y
pip install pandas-ta

echo.
echo Installing alternative TA library if pandas-ta fails...
pip install ta

echo.
echo ========================================
echo Testing imports...
echo ========================================
python -c "import pandas; print('pandas: OK')"
python -c "import numpy; print('numpy: OK')"
python -c "import requests; print('requests: OK')"
python -c "from dotenv import load_dotenv; print('python-dotenv: OK')"

echo.
echo Testing TA libraries...
python -c "try: import pandas_ta; print('pandas-ta: OK'); except: print('pandas-ta: FAILED')"
python -c "try: import ta; print('ta library: OK'); except: print('ta library: FAILED')"

echo.
echo Testing other packages...
python -c "import loguru; print('loguru: OK')"
python -c "import rich; print('rich: OK')"

echo.
echo ========================================
echo Fix Complete!
echo ========================================
pause