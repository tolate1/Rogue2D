@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================================
echo   Rogue 2D: Dungeon Descent - Launching Game...
echo ========================================================

if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" main.py
) else (
    python main.py
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo ========================================================
    echo   [ERROR] Game exited with error code %ERRORLEVEL%.
    echo   Check crash.log or the output above.
    echo ========================================================
    pause
)
