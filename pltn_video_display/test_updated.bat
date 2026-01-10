@echo off
REM Updated test script with new keyboard controls

echo ==========================================
echo PLTN Video Display - Test (Updated)
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
echo.
echo NEW KEYBOARD CONTROLS:
echo   I = IDLE mode (branding screen)
echo   M = MANUAL mode (interactive guide)
echo   A = AUTO mode (video playback)
echo.
echo   UP/DOWN = Adjust pressure
echo   R = Toggle rods
echo   P = Toggle pumps
echo   ESC = Exit
echo.
echo Will start in IDLE mode (branding screen)
echo.
echo Press any key to start...
pause >nul

python video_display_app.py --test --windowed
