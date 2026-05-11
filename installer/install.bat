@echo off
REM AI Meeting Assistant - Windows 安装脚本
REM
REM 用法: install.bat

setlocal enabledelayedexpansion

REM 项目根目录
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

echo.
echo ============================================================
echo   AI Meeting Assistant - 安装程序
echo ============================================================
echo.
echo 开始安装...
echo.

REM ============================================================
REM 检查 Python
REM ============================================================

echo [1/7] 检查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   [错误] 未找到 Python
    echo   请从 https://www.python.org/downloads/ 下载并安装 Python 3.10 或更高版本
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo   [成功] 找到 Python %PYTHON_VERSION%

REM ============================================================
REM 检查 FFmpeg
REM ============================================================

echo.
echo [2/7] 检查 FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo   [警告] FFmpeg 未安装
    echo.
    echo   请从以下地址下载 FFmpeg:
    echo   https://www.gyan.dev/ffmpeg/builds/
    echo.
    echo   下载 ffmpeg-release-essentials.zip 后:
    echo   1. 解压到 C:\ffmpeg
    echo   2. 将 C:\ffmpeg\bin 添加到系统 PATH
    echo.
    pause
    exit /b 1
)

echo   [成功] FFmpeg 已安装

REM ============================================================
REM 创建虚拟环境
REM ============================================================

echo.
echo [3/7] 创建虚拟环境...

if exist .venv (
    echo   [警告] 虚拟环境已存在
    set /p RECREATE="是否重新创建？[y/N]: "
    if /i "!RECREATE!"=="y" (
        rmdir /s /q .venv
        echo   已删除旧虚拟环境
    ) else (
        echo   使用现有虚拟环境
        goto activate_venv
    )
)

python -m venv .venv
if errorlevel 1 (
    echo   [错误] 创建虚拟环境失败
    pause
    exit /b 1
)

echo   [成功] 虚拟环境创建成功

:activate_venv

REM ============================================================
REM 激活虚拟环境并升级 pip
REM ============================================================

echo.
echo [4/7] 激活虚拟环境并升级 pip...

call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo   [错误] 激活虚拟环境失败
    pause
    exit /b 1
)

python -m pip install --upgrade pip
if errorlevel 1 (
    echo   [警告] 升级 pip 失败，继续安装...
)

echo   [成功] pip 已准备就绪

REM ============================================================
REM 安装依赖
REM ============================================================

echo.
echo [5/7] 安装 Python 依赖...
echo   这可能需要几分钟...

pip install -r requirements.txt
if errorlevel 1 (
    echo   [错误] 依赖安装失败
    pause
    exit /b 1
)

echo   [成功] 依赖安装完成

REM ============================================================
REM 安装额外依赖
REM ============================================================

echo.
echo [6/7] 安装额外依赖...

pip install tqdm
pip install python-dotenv

echo   [成功] 额外依赖安装完成

REM ============================================================
REM 运行配置向导
REM ============================================================

echo.
echo [7/7] 配置向导...
echo.

python installer\setup_wizard.py
if errorlevel 1 (
    echo   [警告] 配置向导异常退出
)

REM ============================================================
REM 创建启动脚本
REM ============================================================

echo.
echo 创建启动脚本...

REM CLI 启动脚本
echo @echo off > run.bat
echo REM AI Meeting Assistant - 启动脚本 >> run.bat
echo. >> run.bat
echo cd /d "%%~dp0" >> run.bat
echo call .venv\Scripts\activate.bat >> run.bat
echo python -m meeting_intelligence.cli %%* >> run.bat

echo   [成功] 创建 run.bat

REM ============================================================
REM 安装完成
REM ============================================================

echo.
echo ============================================================
echo   安装完成
echo ============================================================
echo.
echo   [成功] AI Meeting Assistant 已成功安装！
echo.
echo   开始使用:
echo     方式 1: 双击 run.bat
echo     方式 2: 在命令行运行: python -m meeting_intelligence.cli
echo.
echo   文档: README.md
echo.
echo   按任意键退出...
pause >nul
