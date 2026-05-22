@echo off
REM ============================================================
REM Jinni Meeting Intelligence - 快速重启脚本
REM ============================================================
REM
REM 功能：停止所有服务并重新启动
REM 使用：双击此脚本或运行 quick_restart.bat
REM

echo.
echo ========================================
echo   Jinni Meeting Intelligence
echo   快速重启
echo ========================================
echo.
echo [*] 正在停止所有服务...
echo.

REM 调用停止脚本（silent 模式，不等待）
call stop_jinni.bat /silent

echo.
echo [*] 等待2秒...
timeout /t 2 /nobreak >nul

echo.
echo [*] 正在重新启动...
echo.

REM 调用启动脚本
call start_jinni.bat
