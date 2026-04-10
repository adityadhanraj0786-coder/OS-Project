@echo off
setlocal
cd /d "%~dp0os_simulator"
python Main.py
if errorlevel 1 (
    echo.
    echo The simulator closed because of an error.
    pause
)
