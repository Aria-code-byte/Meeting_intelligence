@echo off
echo ================================================
echo 清理端口 8000 - 会议智能后端
echo ================================================
echo.

echo 正在查找占用端口 8000 的进程...
echo.

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING"') do (
    echo 发现进程 PID: %%a
    taskkill /F /PID %%a 2>nul
    if errorlevel 1 (
        echo     [无法结束 - 进程可能已不存在]
    ) else (
        echo     [已成功结束]
    )
)

echo.
echo ================================================
echo 端口 8000 清理完成！
echo ================================================
echo.
echo 现在可以启动后端了：
echo   cd D:\projects\Meeting_intelligence\backend
echo   python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
echo.
pause