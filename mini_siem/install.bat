@echo off
REM Mini SIEM Installation Script for Windows (Development Only)

echo ======================================
echo Mini SIEM - Windows Installation Helper
echo ======================================
echo.

REM Check Python installation
python --version > nul 2>&1
if errorlevel 1 (
    echo [!] Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [+] Python found
python --version

REM Create virtual environment
echo.
echo [+] Creating Python virtual environment...
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo.
echo [+] Installing Python dependencies...
pip install -r requirements.txt -q

echo.
echo ======================================
echo Installation Complete!
echo ======================================
echo.

echo Next steps:
echo.
echo 1. Activate virtual environment:
echo    venv\Scripts\activate.bat
echo.
echo 2. Start Mini SIEM with mock alerts:
echo    python siem_orchestrator.py --mock
echo.
echo 3. In another terminal, start web server:
echo    python app/main.py
echo.
echo 4. Access dashboard:
echo    http://localhost:5000
echo.
echo Note: For actual Snort integration, use Ubuntu/Debian Linux
echo.

pause
