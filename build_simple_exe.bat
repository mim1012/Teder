@echo off
echo ========================================
echo Building Simple EXE with PyInstaller
echo ========================================
echo.

REM Clean previous builds
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist *.spec del *.spec

echo Installing required packages...
pip install pyinstaller python-dotenv pandas pandas-ta requests rich

echo.
echo Building executable...
pyinstaller --onefile ^
    --console ^
    --name TederBot ^
    --hidden-import pandas ^
    --hidden-import numpy ^
    --hidden-import requests ^
    --hidden-import dotenv ^
    --hidden-import rich ^
    --hidden-import pandas_ta ^
    --add-data "src;src" ^
    --add-data "config;config" ^
    --add-data "backtest;backtest" ^
    main_live.py

if exist dist\TederBot.exe (
    echo.
    echo ========================================
    echo BUILD SUCCESS!
    echo ========================================
    echo.
    echo Executable created: dist\TederBot.exe
    echo.
    
    REM Create distribution folder
    if not exist TederBot_Distribution mkdir TederBot_Distribution
    copy dist\TederBot.exe TederBot_Distribution\
    copy .env.example TederBot_Distribution\
    
    echo @echo off > TederBot_Distribution\Run.bat
    echo TederBot.exe >> TederBot_Distribution\Run.bat
    echo pause >> TederBot_Distribution\Run.bat
    
    echo.
    echo Distribution folder: TederBot_Distribution\
    echo Give this folder to users!
) else (
    echo.
    echo BUILD FAILED!
)

pause