@echo off
echo ================================================
echo TederBot Distribution Package Build
echo ================================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed.
    pause
    exit /b 1
)

echo Starting build...
echo.

REM Run build script
python build_dist.py

if %errorlevel% equ 0 (
    echo.
    echo ================================================
    echo Build Complete!
    echo ================================================
    echo.
    echo Please deliver the generated ZIP file to users.
    echo The code is protected.
    echo.
) else (
    echo.
    echo [ERROR] Build failed
    echo.
)

pause