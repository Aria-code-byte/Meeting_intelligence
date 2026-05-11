@echo off
REM AI Meeting Assistant - Windows 启动脚本
REM 自动检测配置并启动相应的界面

setlocal

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"

echo.
echo =============================================================
echo   AI Meeting Assistant
echo =============================================================
echo.

REM 检查虚拟环境
if not exist "%VENV_DIR%" (
    echo [错误] 虚拟环境不存在
    echo        请先运行: installer\install.bat
    pause
    exit /b 1
)

REM 激活虚拟环境
call "%VENV_DIR%\Scripts\activate.bat"

REM 检查是否首次运行
set "CONFIG_DIR=%SCRIPT_DIR%.config"
set "PREFERENCES_FILE=%CONFIG_DIR%\preferences.json"

if not exist "%PREFERENCES_FILE%" (
    echo.
    echo 欢迎使用 AI Meeting Assistant！
    echo.
    echo 检测到首次运行，启动配置向导...
    echo.

    python "%SCRIPT_DIR%\installer\setup_wizard.py"
)

REM 获取界面偏好
set "INTERFACE_MODE=cli"

if exist "%PREFERENCES_FILE%" (
    for /f "delims=" %%i in ('python -c "import json; print(json.load(open(r'%PREFERENCES_FILE%'))['interface_mode'])" 2^>nul') do set "INTERFACE_MODE=%%i"
)

REM 启动相应的界面
if "%INTERFACE_MODE%"=="web" (
    echo 启动 Web 界面...
    echo.
    cd /d "%SCRIPT_DIR%\web_backend"
    streamlit run app.py --server.port 8501
) else (
    echo 启动 CLI 界面...
    echo.
    cd /d "%SCRIPT_DIR%"
    python -m meeting_intelligence.cli %*
)

endlocal
