# Testing and verification

## Supported development baseline

- Windows 10 or Windows 11, 64-bit
- Python 3.10 or newer
- FFmpeg available on `PATH` or at `ffmpeg/ffmpeg.exe`

Install development dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

Run the complete automated baseline:

```powershell
.\verify.ps1
```

The command compiles the Python files, runs Ruff correctness checks, executes all
unit tests, and enforces the initial coverage floor.

## Optional manual smoke test

Use media that you own or are authorized to download. Do not place unstable public
URLs in the automated suite.

1. Launch with `python main.py`.
2. Download one short audio item as MP3.
3. Download one short video item as MP4.
4. Confirm the media opens and contains audio.
5. Download a two-item playlist and confirm the reported count.
6. Cancel a download and confirm no completion record is added.
7. Restart the application and confirm settings and history remain available.
8. If optional dependencies are installed, verify playback, metadata editing, tray
   restoration, and completion notifications.

Live extractor tests remain manual because remote media availability and extractor
behavior change independently of this repository.

