@echo off
REM ============================================================
REM Jinni Meeting Intelligence - 统一启动脚本 (React UI)
REM ============================================================
REM
REM 功能：
REM 1. 清理占用端口 8000 和 5173 的进程
REM 2. 启动后端服务（端口 8000）
REM 3. 启动前端服务（端口 5173）- React + TypeScript + Tailwind
REM 4. 使用最新的 React UI 版本
REM
REM 使用方法：
REM 双击此脚本，或在命令行执行：start_jinni.bat
REM
REM ============================================================

echo.
echo ========================================
echo   Jinni Meeting Intelligence
echo   统一启动脚本 (React UI)
echo ========================================
echo.
echo [1/5] 清理端口占用...
echo.

REM ============================================================
REM 步骤 1: 安全清理端口占用
REM ============================================================

echo [*] 清理端口 8000（后端）...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING"') do (
    taskkill /F /PID %%a >/dev/null 2>&1
)

echo [*] 清理端口 5173（前端 React）...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173.*LISTENING"') do (
    taskkill /F /PID %%a >/dev/null 2>&1
)

echo [*] 等待端口释放...
timeout /t 2 /nobreak >/dev/null

echo     端口清理完成
echo.

REM ============================================================
REM 步骤 2: 启动后端服务
REM ============================================================

echo [2/5] 启动后端服务...
echo.

cd /d "%~dp0"

echo [*] 后端服务：backend/main.py
echo [*] 服务地址：http://localhost:8000
echo [*] API 文档：http://localhost:8000/docs
echo.

start "Jinni Backend" cmd /k "cd /d ""%~dp0backend"" && python main.py"

echo [*] 后端启动命令已执行
echo.

echo [*] 等待后端初始化...
timeout /t 5 /nobreak >/dev/null

echo [*] 检查后端健康状态...
curl -s http://localhost:8000/health >/dev/null 2>&1
if %errorlevel% neq 0 (
    echo [!] 警告：后端可能未启动，请检查错误信息
    echo [*] 如遇问题，请手动检查 backend/main.py 是否存在
) else (
    echo     后端服务启动成功
)
echo.

REM ============================================================
REM 步骤 3: 启动前端服务（React）
REM ============================================================

echo [3/5] 启动前端服务（React）...
echo.

echo [*] 前端服务：web_backend/react-ui
echo [*] 服务地址：http://localhost:5173
echo [*] 技术栈：React + TypeScript + Tailwind + Vite
echo [*] 上传限制：2GB
echo.

start "Jinni React Frontend" cmd /k "cd /d ""%~dp0web_backend\react-ui"" && npm run dev"

echo [*] 前端启动命令已执行
echo.

echo [*] 等待前端初始化（Vite 需要 10-15 秒）...
timeout /t 12 /nobreak >/dev/null

echo [*] 检查前端状态...
curl -s http://localhost:5173 >/dev/null 2>&1
if %errorlevel% neq 0 (
    echo [!] 警告：前端可能仍在启动中，请稍后再试
    echo [*] Vite 服务器可能需要更长时间，请检查命令窗口
) else (
    echo     前端服务启动成功
)
echo.

REM ============================================================
REM 步骤 4: 显示访问信息
REM ============================================================

echo [4/5] 服务访问信息
echo.
echo ========================================
echo   前端地址（React UI）
echo ========================================
echo.
echo   http://localhost:5173
echo.
echo ========================================
echo   后端地址
echo ========================================
echo.
echo   http://localhost:8000
echo   http://localhost:8000/docs
echo.
echo ========================================
echo   启动完成！
echo ========================================
echo.
echo [5/5] 使用说明
echo.
echo 1. 在浏览器中访问：http://localhost:5173
echo 2. React UI 包含：工作台、会议库、模板管理
echo.
echo 3. 停止服务：
echo    - 关闭两个命令提示符窗口
echo    - 或者运行：stop_jinni.bat
echo.
echo 4. 问题排查：
echo    - 如果端口被占用，请运行：stop_jinni.bat
echo    - 如果页面显示异常，请按 Ctrl+Shift+R 强制刷新
echo.
echo ========================================

pause
