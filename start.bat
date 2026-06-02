@echo off
REM AI Meeting Assistant - 启动脚本
REM FastAPI 后端 + React 前端

setlocal

set "PROJECT_DIR=%~dp0"
set "VENV_DIR=%PROJECT_DIR%.venv"
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "FRONTEND_DIR=%PROJECT_DIR%web_backend\react-ui"

echo.
echo ========================================
echo   AI Meeting Assistant
echo ========================================
echo.
echo 正在启动服务...
echo.

REM 检查虚拟环境
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [错误] 虚拟环境不存在
    echo        请先创建: python -m venv .venv
    pause
    exit /b 1
)

REM 激活虚拟环境
call "%VENV_DIR%\Scripts\activate.bat"

REM 启动后端 (端口 8000)
echo [1/2] 启动后端服务 (端口 8000)...
start /B cmd /c "cd /d "%BACKEND_DIR%" && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

REM 等待后端启动
timeout /t 3 /nobreak >/dev/null

REM 启动前端 (端口 5173)
echo [2/2] 启动前端服务 (端口 5173)...
start cmd /c "cd /d "%FRONTEND_DIR%" && npm run dev"

echo.
echo ✅ 服务启动完成！
echo.
echo 📊 后端: http://localhost:8000
echo 🎨 前端: http://localhost:5173
echo.
echo 按任意键关闭此窗口...
pause >/dev/null

endlocal
