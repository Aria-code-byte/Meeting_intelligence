@echo off
REM =============================================================================
REM AI 会议智能助手 - 自动安装脚本 (Windows)
REM =============================================================================

setlocal enabledelayedexpansion

REM 颜色设置（Windows 10+）
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "WARNING=[WARNING]"
set "ERROR=[ERROR]"

REM 打印横幅
echo ============================================================================
echo   AI 会议智能助手 - 自动安装脚本
echo   AI Meeting Assistant - Installation Script
echo ============================================================================
echo.

REM 检查 Python
echo %INFO% 检查 Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR% 未找到 Python，请先安装 Python 3.10+
    echo 访问: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo %SUCCESS% 找到 Python %PYTHON_VERSION%

REM 检查 Python 版本
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% lss 3 (
    echo %ERROR% Python 版本过低，需要 3.10 或更高版本
    pause
    exit /b 1
)

if %MAJOR% equ 3 (
    if %MINOR% lss 10 (
        echo %ERROR% Python 版本过低，需要 3.10 或更高版本
        pause
        exit /b 1
    )
)

REM 检查 Node.js
echo %INFO% 检查 Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR% 未找到 Node.js，请先安装 Node.js 18+
    echo 访问: https://nodejs.org/
    pause
    exit /b 1
)

for /f "tokens=1" %%i in ('node --version') do set NODE_VERSION=%%i
echo %SUCCESS% 找到 Node.js %NODE_VERSION%

REM 检查 FFmpeg
echo %INFO% 检查 FFmpeg...
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo %WARNING% 未找到 FFmpeg
    set FFMPEG_FOUND=0
) else (
    for /f "tokens=1-3" %%a in ('ffmpeg -version 2^>^&1 ^| findstr /r "ffmpeg version"') do (
        echo %SUCCESS% 找到 FFmpeg %%a %%b %%c
    )
    set FFMPEG_FOUND=1
)

REM 提示安装 FFmpeg
if %FFMPEG_FOUND% equ 0 (
    echo.
    echo %WARNING% FFmpeg 未安装，请手动安装：
    echo.
    echo 1. 访问: https://www.gyan.dev/ffmpeg/builds/
    echo 2. 下载 ffmpeg-release-essentials.zip
    echo 3. 解压到 C:\ffmpeg
    echo 4. 添加 C:\ffmpeg\bin 到系统环境变量 PATH
    echo 5. 重启命令提示符
    echo.
    set /p CONTINUE="FFmpeg 未安装，是否继续？(Y/N): "
    if /i not "%CONTINUE%"=="Y" (
        pause
        exit /b 1
    )
)

REM 创建虚拟环境
echo %INFO% 创建 Python 虚拟环境...
if exist .venv (
    echo %WARNING% 虚拟环境已存在，跳过创建
) else (
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo %ERROR% 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo %SUCCESS% 虚拟环境创建完成
)

REM 激活虚拟环境
echo %INFO% 激活虚拟环境...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo %ERROR% 虚拟环境激活失败
    pause
    exit /b 1
)
echo %SUCCESS% 虚拟环境已激活

REM 升级 pip
echo %INFO% 升级 pip...
python -m pip install --upgrade pip -q
if %errorlevel% neq 0 (
    echo %WARNING% pip 升级失败，继续安装...
) else (
    echo %SUCCESS% pip 升级完成
)

REM 安装后端依赖
echo %INFO% 安装后端依赖...
if exist backend\requirements.txt (
    pip install -r backend\requirements.txt -q
    if %errorlevel% neq 0 (
        echo %ERROR% 后端依赖安装失败
        pause
        exit /b 1
    )
    echo %SUCCESS% 后端依赖安装完成
) else (
    echo %ERROR% 未找到 backend\requirements.txt
    pause
    exit /b 1
)

REM 配置环境变量
echo %INFO% 配置环境变量...
if not exist backend\.env (
    if exist backend\.env.example (
        copy backend\.env.example backend\.env >nul
        echo %SUCCESS% 已创建 backend\.env（使用默认配置）
        echo %WARNING% 请编辑 backend\.env 配置您的 API Key
    ) else (
        echo %WARNING% 未找到 backend\.env.example
    )
) else (
    echo %INFO% backend\.env 已存在，跳过
)

REM 安装前端依赖
echo %INFO% 安装前端依赖...
if exist web_backend\react-ui (
    cd web_backend\react-ui

    where npm >nul 2>&1
    if %errorlevel% neq 0 (
        echo %ERROR% 未找到 npm
        cd ..\..
        pause
        exit /b 1
    )

    call npm install
    if %errorlevel% neq 0 (
        echo %ERROR% 前端依赖安装失败
        cd ..\..
        pause
        exit /b 1
    )
    echo %SUCCESS% 前端依赖安装完成

    cd ..\..
) else (
    echo %ERROR% 未找到 web_backend\react-ui 目录
    pause
    exit /b 1
)

REM 创建启动脚本
echo %INFO% 创建启动脚本...

REM 启动脚本
(
echo @echo off
echo REM 启动 AI 会议智能助手
echo.
echo echo 启动 AI 会议智能助手...
echo.
echo REM 检查虚拟环境
echo if not exist .venv^(
echo     echo 错误: 虚拟环境不存在，请先运行 install.bat
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM 激活虚拟环境并启动后端
echo call .venv\Scripts\activate.bat
echo echo 启动后端服务...
echo start /B python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload ^> .backend.log 2^>^&1
echo.
echo REM 等待后端启动
echo timeout /t 3 /nobreak ^>nul
echo.
echo REM 启动前端
echo echo 启动前端服务...
echo cd web_backend\react-ui
echo start /B npm run dev ^> ..\..\.frontend.log 2^>^&1
echo cd ..\..
echo.
echo echo ==========================================
echo echo   AI 会议智能助手已启动！
echo echo ==========================================
echo echo   前端: http://localhost:5173
echo echo   后端: http://localhost:8000
echo echo   API文档: http://localhost:8000/docs
echo echo ==========================================
echo echo.
echo echo 停止服务: stop.bat
echo echo 查看日志: type .backend.log 或 .frontend.log
echo pause
) > start.bat

echo %SUCCESS% 启动脚本创建完成 (start.bat)

REM 停止脚本
(
echo @echo off
echo REM 停止 AI 会议智能助手
echo.
echo echo 停止 AI 会议智能助手...
echo.
echo taskkill /F /IM uvicorn.exe 2^>nul
echo taskkill /F /IM node.exe 2^>nul
echo.
echo echo 服务已停止
echo pause
) > stop.bat

echo %SUCCESS% 停止脚本创建完成 (stop.bat)

REM 安装完成
echo.
echo ============================================================================
echo   安装完成！
echo ============================================================================
echo.
echo 下一步操作：
echo.
echo 1. 配置环境变量（如果需要使用 AI 功能）：
echo    编辑 backend\.env 文件
echo.
echo 2. 启动服务：
echo    start.bat
echo.
echo 3. 访问应用：
echo    http://localhost:5173
echo.
echo 4. 停止服务：
echo    stop.bat
echo.
echo 注意: 首次运行会下载 Whisper 模型，可能需要较长时间
echo.

pause
