@echo off
REM OpenSkills installation to target project script (Windows)
REM Usage: install_to_project.bat <target_project_path>

setlocal enabledelayedexpansion

REM Check parameters
if "%~1"=="" (
    echo ========================================
    echo OpenSkills Installation to Target Project
    echo ========================================
    echo.
    echo Usage: install_to_project.bat ^<target_project_path^>
    echo.
    echo Examples:
    echo   install_to_project.bat C:\my-project
    echo   install_to_project.bat ..\my-project
    echo.
    pause
    exit /b 1
)

set TARGET_PROJECT=%~1

echo ========================================
echo OpenSkills Installation to Target Project
echo ========================================
echo.
echo Target project path: %TARGET_PROJECT%
echo.

REM Check if target project path exists
if not exist "%TARGET_PROJECT%" (
    echo [Error] Target project path does not exist: %TARGET_PROJECT%
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Enter target project directory
pushd "%TARGET_PROJECT%"
if errorlevel 1 (
    echo [Error] Cannot enter target project directory: %TARGET_PROJECT%
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment in target project...
if exist ".venv" (
    echo [Info] Virtual environment already exists, removing...
    rmdir /s /q .venv
)

python -m venv .venv
if errorlevel 1 (
    echo [Error] Failed to create virtual environment.
    popd
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [3/5] Installing OpenSkills...
REM Get absolute path of current script directory
set SCRIPT_DIR=%~dp0

pip install -e "%SCRIPT_DIR%."
if errorlevel 1 (
    echo [Error] Failed to install OpenSkills.
    popd
    pause
    exit /b 1
)

echo [4/5] Adding to .gitignore...
set GITIGNORE=.gitignore
set FOUND=0

if exist "%GITIGNORE%" (
    findstr /C:".venv" "%GITIGNORE%" >nul 2>&1
    if not errorlevel 1 (
        set FOUND=1
    )
)

if %FOUND%==0 (
    echo. >> "%GITIGNORE%"
    echo # OpenSkills virtual environment >> "%GITIGNORE%"
    echo .venv/ >> "%GITIGNORE%"
    echo [Info] Added .venv to .gitignore
) else (
    echo [Info] .venv already in .gitignore, skipped
)

echo [5/5] Creating startup script...
REM Create convenient startup script
echo @echo off > openskills.bat
echo call .venv\Scripts\activate.bat >> openskills.bat
echo openskills %%* >> openskills.bat
echo deactivate >> openskills.bat

echo.
echo ========================================
echo [Success] OpenSkills Installation Complete!
echo ========================================
echo.
echo Usage:
echo   1. Activate virtual environment: .venv\Scripts\activate
echo   2. Use command: openskills --help
echo   3. Or use quick command: openskills.bat --help
echo   4. Deactivate virtual environment: deactivate
echo.
echo Note:
echo   - Virtual environment added to .gitignore, will not commit to git
echo   - Created openskills.bat quick script in project root
echo.

popd