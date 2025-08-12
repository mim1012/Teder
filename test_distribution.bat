@echo off
echo ================================================
echo Testing Distribution Package
echo ================================================
echo.

REM Extract and test the distribution
if exist test_dist rd /s /q test_dist
mkdir test_dist
cd test_dist

echo Extracting package...
powershell -command "Expand-Archive -Path '..\TederBot_v1.0.0_20250807_233011.zip' -DestinationPath '.' -Force"

echo.
echo Contents:
dir /B

echo.
echo Testing Python import...
python -c "import sys; sys.path.insert(0, 'bot'); import main_live; print('[OK] Module import successful')"

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Distribution package is working!
) else (
    echo.
    echo [ERROR] Failed to import modules
)

cd ..
pause