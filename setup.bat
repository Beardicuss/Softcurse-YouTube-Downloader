@echo off
title Softcurse // YouTube Downloader v4 - Setup
color 0B
echo.
echo  ╔════════════════════════════════════════════════╗
echo  ║  ◈  SOFTCURSE  ◈  YT DOWNLOADER v4 SETUP    ║
echo  ╚════════════════════════════════════════════════╝
echo.

set PYTHON_CMD=
python --version >nul 2>&1
if not errorlevel 1 ( set PYTHON_CMD=python & echo  [OK] Found: python & goto :install )
py --version >nul 2>&1
if not errorlevel 1 ( set PYTHON_CMD=py & echo  [OK] Found: py launcher & goto :install )
echo  [ERROR] Python not found! Install from https://python.org
pause & exit /b 1

:install
echo  [*] Core: yt-dlp...
%PYTHON_CMD% -m pip install yt-dlp --upgrade -q
echo  [*] Thumbnails: Pillow...
%PYTHON_CMD% -m pip install Pillow -q
echo  [*] Metadata: mutagen...
%PYTHON_CMD% -m pip install mutagen -q
echo  [*] Tray + notifications: pystray, plyer...
%PYTHON_CMD% -m pip install pystray plyer -q
echo  [*] Mini player: pygame...
%PYTHON_CMD% -m pip install pygame -q

ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [WARN] ffmpeg not found.
    echo    Install:  winget install ffmpeg
    echo    Or place ffmpeg.exe in the ./ffmpeg/ folder.
) else (
    echo  [OK] ffmpeg found.
)

echo.
echo  ╔════════════════════════════════════════════════╗
echo  ║      SETUP COMPLETE! Run launch.bat           ║
echo  ╚════════════════════════════════════════════════╝
pause
