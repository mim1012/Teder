@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo Installing Minimal Required Packages
echo ========================================
echo.

REM Activate virtual environment
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
)

echo.
echo Installing essential packages only...
echo.

REM Core packages only
pip install pandas
pip install numpy
pip install requests
pip install python-dotenv

REM Optional but useful
pip install loguru
pip install rich

echo.
echo ========================================
echo Testing imports...
echo ========================================
echo.

python -c "import pandas; print('pandas: OK')"
python -c "import numpy; print('numpy: OK')"
python -c "import requests; print('requests: OK')"
python -c "from dotenv import load_dotenv; print('python-dotenv: OK')"
python -c "try: import loguru; print('loguru: OK'); except: print('loguru: Optional')"
python -c "try: import rich; print('rich: OK'); except: print('rich: Optional')"

echo.
echo ========================================
echo Minimal installation complete!
echo You can now run: run_test_en.bat
echo ========================================
pause