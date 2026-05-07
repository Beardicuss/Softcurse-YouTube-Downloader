@echo off
title Softcurse // Media Downloader v1.0 Build
color 0B
echo.
echo  ╔════════════════════════════════════════════════╗
echo  ║    BUILDING SOFTCURSE MEDIA DOWNLOADER v1.0    ║
echo  ╚════════════════════════════════════════════════╝
echo.

set PYTHON_CMD=python
python --version >nul 2>&1
if errorlevel 1 ( set PYTHON_CMD=py )

%PYTHON_CMD% -m pip install pyinstaller -q

echo  [*] Collecting hidden imports...
set HIDDEN=--hidden-import=yt_dlp --hidden-import=mutagen --hidden-import=PIL
set HIDDEN=%HIDDEN% --hidden-import=pygame --hidden-import=pystray --hidden-import=plyer

if exist "ffmpeg\ffmpeg.exe" (
    echo  [*] Bundling with ffmpeg.exe...
    %PYTHON_CMD% -m PyInstaller --onefile --windowed ^
        --name "Softcurse_Media_Downloader" ^
        --icon "assets\yt.ico" ^
        --add-data "ffmpeg\ffmpeg.exe;ffmpeg" ^
        %HIDDEN% main.py
) else (
    echo  [!] No bundled ffmpeg — users need ffmpeg installed separately.
    %PYTHON_CMD% -m PyInstaller --onefile --windowed ^
        --name "Softcurse_Media_Downloader" ^
        --icon "assets\yt.ico" ^
        %HIDDEN% main.py
)

echo.
echo  [DONE] dist\Softcurse_Media_Downloader.exe
echo  [NEXT] Run installer\softcurse_installer.iss in Inno Setup to build installer.
pause
