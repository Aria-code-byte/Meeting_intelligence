@echo off
REM Jinni Meeting Elf - v12 UI Fixed Stable Version
REM 最终验收通过版本

echo ========================================
echo Jinni Meeting Elf v12 UI Fixed Stable
echo ========================================
echo.
echo [验收通过版本]
echo - Step 2: UI 已治理，调试信息已隐藏
echo - Step 3: 模板管理已改为折叠面板
echo - DEBUG_MODE = False
echo.
echo [启动中] Streamlit 服务
echo [访问地址] http://localhost:8501
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo [!] 虚拟环境不存在，请先运行安装脚本
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
streamlit run app_working_v12_ui_fixed_stable.py --server.port 8501

pause
