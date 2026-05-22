@echo off
echo ================================================
echo FFmpeg Quick Installer for Windows
echo ================================================
echo.

REM 检查是否已安装 ffmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] FFmpeg is already installed
    ffmpeg -version | findstr "ffmpeg version"
    echo.
    echo You can now restart the backend and use real transcription!
    pause
    exit /b 0
)

echo [INFO] FFmpeg not found, installing...
echo.

REM 检查是否有 Chocolatey
choco --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Using Chocolatey to install FFmpeg...
    choco install ffmpeg -y
    if %errorlevel% equ 0 (
        echo.
        echo [SUCCESS] FFmpeg installed successfully!
        echo Please restart your command prompt and run: ffmpeg -version
        pause
        exit /b 0
    ) else (
        echo [ERROR] Chocolatey installation failed
        goto :manual_install
    )
) else (
    echo [INFO] Chocolatey not found
    goto :manual_install
)

:manual_install
echo.
echo ================================================
echo Manual Installation Instructions
echo ================================================
echo.
echo OPTION 1: Install Chocolatey and FFmpeg
echo   1. Open PowerShell as Administrator
echo   2. Run: Set-ExecutionPolicy Bypass -Scope Process -Force
echo   3. Run: [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
echo   4. Run: iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
echo   5. Run: choco install ffmpeg
echo.
echo OPTION 2: Download FFmpeg manually
echo   1. Visit: https://ffmpeg.org/download.html#build-windows
echo   2. Download: Windows 64-bit build
echo   3. Extract to: C:\ffmpeg
echo   4. Add C:\ffmpeg\bin to PATH
echo   5. Restart command prompt
echo.
echo OPTION 3: Use a pre-built package
echo   1. Visit: https://www.gyan.dev/ffmpeg/builds/
echo   2. Download: ffmpeg-release-essentials.zip
echo   3. Extract and add to PATH
echo.
pause

:end
