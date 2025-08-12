@echo off
echo ======================================
echo SPLIT BUY STRATEGY BACKTEST
echo ======================================
echo.

REM 가상환경 활성화 (있는 경우)
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM 필요한 패키지 설치 확인
echo Checking required packages...
python -c "import pandas, pandas_ta, numpy, matplotlib" 2>nul
if %errorlevel% neq 0 (
    echo Installing required packages...
    pip install pandas pandas-ta numpy matplotlib
)

echo.
echo Running Split Buy Strategy Backtest...
echo This will generate sample data and test the strategy
echo.

REM 백테스트 실행
python test_split_strategy.py

if %errorlevel% neq 0 (
    echo.
    echo Backtest failed with error code: %errorlevel%
    pause
)

echo.
echo Backtest completed.
pause