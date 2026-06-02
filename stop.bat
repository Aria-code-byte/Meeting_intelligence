@echo off
REM AI Meeting Assistant - 停止脚本

echo.
echo ========================================
echo   停止 AI Meeting Assistant
echo ========================================
echo.

REM 停止后端 (端口 8000)
echo [1/2] 停止后端服务...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    taskkill /F /PID %%a 2>/dev/null
)

REM 停止前端 (端口 5173)
echo [2/2] 停止前端服务...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5173" ^| find "LISTENING"') do (
    taskkill /F /PID %%a 2>/dev/null
)

echo.
echo ✅ 服务已停止
echo.
pause
