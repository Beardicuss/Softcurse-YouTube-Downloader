@echo off
title Softcurse // YouTube Downloader
cd /d "%~dp0"

REM Try python first, then py launcher
python main.py 2>nul
if not errorlevel 1 goto :eof

py main.py 2>nul
if not errorlevel 1 goto :eof

echo.
echo  [ERROR] Could not launch the app.
echo  Make sure Python is installed and run setup.bat first.
pause
