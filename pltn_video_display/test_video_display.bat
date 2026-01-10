@echo off
REM Quick test script for PLTN Video Display (Windows)

echo ==========================================
echo PLTN Video Display - Quick Test
echo ==========================================
echo.

REM Check pygame
python -c "import pygame" 2>nul
if errorlevel 1 (
    echo [ERROR] pygame not installed
    echo    Install: pip install pygame
    pause
    exit /b 1
) else (
    echo [OK] pygame installed
)

echo.
echo Starting test mode (windowed)...
echo Controls:
echo   1 = IDLE mode
echo   2 = AUTO mode
echo   3 = MANUAL mode
echo   UP/DOWN = Adjust values
echo   R = Toggle rods
echo   P = Toggle pumps
echo   ESC = Exit
echo.
echo Press any key to start...
pause >nul

python video_display_app.py --test --windowed
