@echo off
REM OpenSkills 安装到目标项目脚本 (Windows)
REM 用法: install_to_project.bat <目标项目路径>

setlocal enabledelayedexpansion

REM 检查参数
if "%~1"=="" (
    echo ========================================
    echo OpenSkills 安装到目标项目
    echo ========================================
    echo.
    echo 用法: install_to_project.bat ^<目标项目路径^>
    echo.
    echo 示例:
    echo   install_to_project.bat C:\my-project
    echo   install_to_project.bat ..\my-project
    echo.
    pause
    exit /b 1
)

set TARGET_PROJECT=%~1

echo ========================================
echo OpenSkills 安装到目标项目
echo ========================================
echo.
echo 目标项目路径: %TARGET_PROJECT%
echo.

REM 检查目标项目路径是否存在
if not exist "%TARGET_PROJECT%" (
    echo [错误] 目标项目路径不存在: %TARGET_PROJECT%
    pause
    exit /b 1
)

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python。请先安装Python 3.8或更高版本。
    pause
    exit /b 1
)

REM 进入目标项目目录
pushd "%TARGET_PROJECT%"
if errorlevel 1 (
    echo [错误] 无法进入目标项目目录: %TARGET_PROJECT%
    pause
    exit /b 1
)

echo [1/5] 在目标项目中创建虚拟环境...
if exist ".venv" (
    echo [提示] 虚拟环境已存在，正在移除...
    rmdir /s /q .venv
)

python -m venv .venv
if errorlevel 1 (
    echo [错误] 创建虚拟环境失败。
    popd
    pause
    exit /b 1
)

echo [2/5] 激活虚拟环境...
call .venv\Scripts\activate.bat

echo [3/5] 安装OpenSkills...
REM 获取当前脚本所在目录的绝对路径
set SCRIPT_DIR=%~dp0

pip install -e "%SCRIPT_DIR%."
if errorlevel 1 (
    echo [错误] 安装OpenSkills失败。
    popd
    pause
    exit /b 1
)

echo [4/5] 添加到.gitignore...
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
    echo [提示] 已添加 .venv 到 .gitignore
) else (
    echo [提示] .venv 已在 .gitignore 中，跳过
)

echo [5/5] 创建启动脚本...
REM 创建便捷的启动脚本
echo @echo off > openskills.bat
echo call .venv\Scripts\activate.bat >> openskills.bat
echo openskills %%* >> openskills.bat
echo deactivate >> openskills.bat

echo.
echo ========================================
echo [成功] OpenSkills安装完成！
echo ========================================
echo.
echo 使用说明：
echo   1. 激活虚拟环境: .venv\Scripts\activate
echo   2. 使用命令: openskills --help
echo   3. 或使用快捷命令: openskills.bat --help
echo   4. 退出虚拟环境: deactivate
echo.
echo 注意：
echo   - 虚拟环境已添加到 .gitignore，不会提交到git
echo   - 项目根目录已创建 openskills.bat 快捷脚本
echo.

popd