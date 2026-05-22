@echo off
REM Jinni Meeting Intelligence - Backend API Startup Script
REM 后端服务启动脚本

echo ========================================
echo Jinni Meeting Intelligence Backend
echo ========================================
echo.

echo [1/3] 检查虚拟环境...
cd /d "%~dp0"

if not exist "..\.venv\Scripts\activate.bat" (
    echo [!] 虚拟环境不存在，请先在项目根目录运行安装脚本
    pause
    exit /b 1
)

echo [2/3] 激活虚拟环境并安装依赖...
call ..\.venv\Scripts\activate.bat

echo 正在检查并安装后端依赖...
pip install -q fastapi uvicorn python-multipart pydantic

echo [3/3] 启动后端服务...
echo.
echo [启动中] FastAPI 服务
echo [后端地址] http://localhost:8000
echo [API 文档] http://localhost:8000/docs
echo.
echo [*] 按 Ctrl+C 停止服务
echo.

python -m uvicorn main:app --reload --port 8000

pause
