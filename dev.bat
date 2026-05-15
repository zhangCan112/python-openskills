@echo off
if "%~1"=="" goto install
if "%~1"=="install" goto install
if "%~1"=="install-dev" goto install-dev
if "%~1"=="uninstall" goto uninstall
if "%~1"=="clean" goto clean
if "%~1"=="test" goto test
goto usage

:install
pip install --force-reinstall --no-deps .
goto end

:install-dev
pip install --force-reinstall --no-deps -e .
goto end

:uninstall
pip uninstall -y openskills
goto end

:clean
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist openskills.egg-info rmdir /s /q openskills.egg-info
for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
goto end

:test
python -m pytest tests/ -v
goto end

:usage
echo Usage: %~nx0 [install^|install-dev^|uninstall^|clean^|test]
echo.
echo   install      Install from source (default)
echo   install-dev  Install in editable mode
echo   uninstall    Uninstall openskills
echo   clean        Remove build artifacts
echo   test         Run tests
goto end

:end
