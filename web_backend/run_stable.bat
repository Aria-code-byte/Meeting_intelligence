@echo off
echo ======================================
echo Jinni Meeting Elf - Stable Version v8
echo ======================================
echo.
echo Starting stable version on port 8501...
echo.

cd /d "%~dp0"
call .venv\Scripts\activate
streamlit run app_working_v8_stable.py --server.port 8501

pause
