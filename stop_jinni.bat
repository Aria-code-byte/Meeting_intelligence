@echo off
REM ============================================================
REM Jinni Meeting Intelligence - 停止服务脚本
REM ============================================================

echo.
echo ========================================
echo   Jinni Meeting Intelligence
echo   停止所有服务
echo ========================================
echo.

if "%1"=="/silent" goto :silent_stop

echo [*] 正在停止服务...
echo.

:silent_stop
REM 停止占用端口 8000 的进程（后端）
if "%1"=="/silent" goto :skip_msg_1
echo [*] 停止后端服务（端口 8000）...
:skip_msg_1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM 停止占用端口 8501 的进程（前端）
if "%1"=="/silent" goto :skip_msg_2
echo [*] 停止前端服务（端口 8501）...
:skip_msg_2
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

if "%1"=="/silent" goto :skip_wait

echo [*] 等待进程完全停止...
timeout /t 3 /nobreak >nul

echo.
echo [*] 检查端口状态...
netstat -ano | findstr ":8000.*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [!] 8000 端口仍被占用
) else (
    echo     8000 端口已释放
)

netstat -ano | findstr ":5173.*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [!] 8501 端口仍被占用
) else (
    echo     8501 端口已释放
)

echo.
echo ========================================
echo   所有服务已停止
echo ========================================
echo.
echo [*] 如果端口仍被占用，请：
echo     1. 打开任务管理器（Ctrl+Shift+Esc）
echo     2. 查找占用端口 8000 或 8501 的进程
echo     3. 手动结束这些进程
echo.

pause
exit /b 0

:skip_wait
exit /b 0
