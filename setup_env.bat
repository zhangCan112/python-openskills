@echo off
REM OpenSkills 虚拟环境设置脚本 (Windows)

echo ========================================
echo OpenSkills 虚拟环境设置
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python。请先安装Python 3.8或更高版本。
    pause
    exit /b 1
)

REM 检查虚拟环境是否已存在
if exist ".venv" (
    echo [提示] 虚拟环境已存在，正在移除...
    rmdir /s /q .venv
)

echo [1/3] 创建虚拟环境...
python -m venv .venv
if errorlevel 1 (
    echo [错误] 创建虚拟环境失败。
    pause
    exit /b 1
)

echo [2/3] 激活虚拟环境...
call .venv\Scripts\activate.bat

echo [3/3] 安装依赖...
pip install -e .
if errorlevel 1 (
    echo [错误] 安装依赖失败。
    pause
    exit /b 1
)

echo.
echo ========================================
echo [成功] 虚拟环境设置完成！
echo ========================================
echo.
echo 使用说明：
echo   1. 激活虚拟环境: .venv\Scripts\activate.bat
echo   2. 使用命令: openskills --help
echo   3. 退出虚拟环境: deactivate
echo.
pause