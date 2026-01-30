@echo off
REM OpenSkills virtual environment setup script (Windows)

echo ========================================
echo OpenSkills Virtual Environment Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if virtual environment already exists
if exist ".venv" (
    echo [Info] Virtual environment already exists, removing...
    rmdir /s /q .venv
)

echo [1/3] Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo [Error] Failed to create virtual environment.
    pause
    exit /b 1
)

echo [2/3] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [3/3] Installing dependencies...
pip install -e .
if errorlevel 1 (
    echo [Error] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo ========================================
echo [Success] Virtual Environment Setup Complete!
echo ========================================
echo.
echo Usage:
echo   1. Activate virtual environment: .venv\Scripts\activate.bat
echo   2. Use command: openskills --help
echo   3. Deactivate virtual environment: deactivate
echo.
pause