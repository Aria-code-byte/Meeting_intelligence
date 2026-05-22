@echo off
REM AI Meeting Assistant - CLI Launcher
REM 启动命令行版本

echo ==================================================
echo   AI Meeting Assistant - CLI Version
echo ==================================================
echo.
echo Starting CLI with DeepSeek LLM...
echo.

REM 设置UTF-8编码
chcp 65001 >nul 2>&1

REM 运行CLI版本
python meeting_cli.py --llm deepseek

pause