@echo off
chcp 65001 > nul
echo ========================================================
echo   Rogue 2D: Dungeon Descent - Building Standalone EXE
echo ========================================================
cd /d "%~dp0"
if exist ".\.venv\Scripts\python.exe" (
    .\.venv\Scripts\python.exe scripts\build_exe.py
) else (
    python scripts\build_exe.py
)
if %ERRORLEVEL% equ 0 (
    echo.
    echo [BUILD SUCCESSFUL] Rogue2.exe is ready in this folder!
) else (
    echo.
    echo [BUILD FAILED] Check the errors above.
)
echo.
pause
