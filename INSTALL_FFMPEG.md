@echo off
echo ================================================
echo 安装 ffmpeg - 支持 Windows
echo ================================================
echo.

echo 方法 1：使用 winget 安装（推荐）
echo ----------------------------------------
winget install ffmpeg
echo.

echo 方法 2：手动下载安装
echo ----------------------------------------
echo 1. 访问：https://www.gyan.dev/ffmpeg/builds/
echo 2. 下载 "ffmpeg-release-essentials.zip"
echo 3. 解压到 C:\ffmpeg
echo 4. 添加 C:\ffmpeg\bin 到系统 PATH
echo.

echo 方法 3：使用 Chocolatey
echo ----------------------------------------
choco install ffmpeg
echo.

echo ================================================
echo 安装完成后，重启系统并重新运行会议智能系统
echo ================================================
pause