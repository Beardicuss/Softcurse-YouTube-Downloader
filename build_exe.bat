@echo off
setlocal
set /p APP_VERSION=<VERSION
title Softcurse // Media Downloader v%APP_VERSION% Build
color 0B
echo.
echo  ==================================================
echo        BUILDING SOFTCURSE MEDIA DOWNLOADER v%APP_VERSION%
echo  ==================================================
echo.

set PYTHON_CMD=python
python --version >nul 2>&1
if errorlevel 1 ( set PYTHON_CMD=py )

%PYTHON_CMD% -m pip install --require-hashes -r requirements-lock.txt
if errorlevel 1 (
    echo  [ERROR] Dependency installation failed. Build aborted.
    exit /b 1
)

echo  [*] Collecting hidden imports...
set HIDDEN=--hidden-import=yt_dlp --hidden-import=mutagen --hidden-import=PIL
set HIDDEN=%HIDDEN% --hidden-import=pygame --hidden-import=pystray --hidden-import=plyer

echo  [*] Building executable...
%PYTHON_CMD% tools\generate_version_info.py
if errorlevel 1 (
    echo  [ERROR] Version metadata generation failed.
    exit /b 1
)

%PYTHON_CMD% -m PyInstaller --onefile --windowed ^
    --name "Softcurse_Media_Downloader" ^
    --icon "assets\yt.ico" ^
    --add-data "assets;assets" ^
    --add-data "VERSION;." ^
    --version-file "build\version_info.txt" ^
    --clean --noconfirm ^
    %HIDDEN% main.py
if errorlevel 1 (
    echo  [ERROR] PyInstaller failed. No release was produced.
    exit /b 1
)

echo.
echo  [DONE] dist\Softcurse_Media_Downloader.exe
%PYTHON_CMD% tools\write_checksum.py "dist\Softcurse_Media_Downloader.exe"
if errorlevel 1 (
    echo  [ERROR] Checksum generation failed.
    exit /b 1
)
echo  [DONE] dist\Softcurse_Media_Downloader.exe.sha256
echo  [NEXT] Run installer\softcurse_installer.iss in Inno Setup to build installer.
