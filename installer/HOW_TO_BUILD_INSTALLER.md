# How to Build the Windows Installer (.exe)

## Prerequisites
1. **Inno Setup 6** — https://jrsoftware.org/isdl.php (free)
2. **PyInstaller** — run `build_exe.bat` first to create the standalone `.exe`
3. Optional: place `ffmpeg.exe` in the `ffmpeg/` folder to bundle it

## Step-by-Step

### Step 1 — Build the standalone .exe
```
build_exe.bat
```
This creates `dist/Softcurse_YT_Downloader.exe` using PyInstaller.

### Step 2 — Build the installer
Open Inno Setup Compiler and:
- File → Open → select `installer/softcurse_installer.iss`
- Press **Ctrl+F9** (Build) or click the green play button
- Output: `installer/Output/Softcurse_YT_Downloader_v4_Setup.exe`

### What the installer does
- Installs `Softcurse_YT_Downloader.exe` to `Program Files` (or user folder)
- Optionally bundles `ffmpeg.exe` if present in `./ffmpeg/`
- Creates Start Menu shortcut
- Optional: Desktop shortcut, startup entry
- Includes uninstaller
- Shows feature list during installation
- Offers to launch app after install

## Distribution
The resulting `Softcurse_YT_Downloader_v4_Setup.exe` is:
- A single self-contained installer (~15–30 MB with ffmpeg)
- No Python required on end-user machine
- Works on Windows 10/11 64-bit
