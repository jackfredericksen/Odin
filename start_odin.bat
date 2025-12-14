@echo off
echo ========================================
echo   Starting Odin Bitcoin Trading Bot
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Python installation...
python --version
echo.

echo Starting Odin server...
echo Dashboard will be available at: http://localhost:8000
echo API documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python -m odin.main

pause
