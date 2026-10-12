# How to build the Windows installer

## Prerequisites

1. Windows 10 or 11, 64-bit.
2. Python 3.10 or newer.
3. Inno Setup 6 or 7.
4. `ffmpeg.exe` in `../ffmpeg/` when producing a self-contained installer.

The application version comes from `../VERSION`. Build dependencies are locked with
hashes in `../requirements-lock.txt`.

## Build

From the repository root:

```powershell
.\build_exe.bat
.\installer\build_installer.ps1
```

The first command creates the application executable and its SHA-256 checksum in
`dist/`. The second compiles the versioned installer and creates a matching checksum
in `installer/Output/`.

## Release validation

- Run `../verify.ps1` before building.
- Test the packaged executable and installer on a clean Windows machine.
- Confirm FFmpeg is reported as ready by the application's System Readiness screen.
- Confirm install, upgrade, launch, update-check, and uninstall behavior.
- Code-sign the executable and installer before publication when a signing certificate
  is available.

The installer uses per-user installation by default, creates optional desktop/startup
shortcuts, and preserves user settings and history during uninstall.
