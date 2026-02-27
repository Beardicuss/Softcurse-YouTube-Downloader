# Softcurse // YouTube Downloader
### MP3 & MP4 Converter — Cyberpunk Edition

```
╔══════════════════════════════════════════╗
║   ◈  S O F T C U R S E  ◈              ║
║   [ YT2MP3 // SOFTCURSE ]              ║
║   YouTube → MP3 / MP4 Downloader       ║
╚══════════════════════════════════════════╝
```

---

## Features

- **MP3 Mode** — download audio, auto-convert, quality 128–320 kbps
- **MP4 Mode** — download video at best / 1080p / 720p / 480p / 360p
- **Playlist support** — download entire YouTube playlists in one click
- **Real-time progress** — neon progress bar with speed and ETA
- **Auto-installs yt-dlp** on first launch
- **Cyberpunk UI** — neon cyan/magenta/orange, grid background, glitch effects
- **Remembers settings** — last folder, quality preference

---

## Quick Start

### Requirements
- **Python 3.10+** — https://python.org (check *Add Python to PATH*)
- **ffmpeg** — required for MP3 conversion and MP4 merging

### Step 1 — Install ffmpeg
```
winget install ffmpeg
```
Or download from https://ffmpeg.org and place `ffmpeg.exe` in the `ffmpeg/` folder.

### Step 2 — Run setup
```
setup.bat
```

### Step 3 — Launch
```
launch.bat
```

---

## How to Use

1. Paste a YouTube URL (single video or playlist)
2. Choose output folder
3. Click **MP3** or **MP4** tab at the top
4. Select quality (kbps for audio, resolution for video)
5. Enable **PLAYLIST MODE** for playlists
6. Click **[ ♪ DOWNLOAD MP3 ]** or **[ ▶ DOWNLOAD MP4 ]**

---

## Build Standalone .EXE

To distribute to others without needing Python:

1. Place `ffmpeg.exe` in the `ffmpeg/` folder
2. Run `build_exe.bat`
3. Find `Softcurse_YT_Downloader.exe` in the `dist/` folder

---

## File Structure

```
Softcurse YT Downloader/
├── main.py           ← Entry point
├── gui.py            ← Cyberpunk UI (MP3/MP4 tabs, neon, glitch)
├── downloader.py     ← yt-dlp + ffmpeg logic (MP3 + MP4)
├── config.py         ← Settings persistence
├── requirements.txt
├── setup.bat         ← Install dependencies (supports python & py)
├── launch.bat        ← Launch the app (supports python & py)
├── build_exe.bat     ← Package as .exe
└── ffmpeg/           ← Drop ffmpeg.exe here (optional)
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ffmpeg not found` | `winget install ffmpeg` or place `ffmpeg.exe` in `./ffmpeg/` |
| `yt-dlp not found` | `pip install yt-dlp` or run `setup.bat` |
| Python not found | Install from python.org, check "Add to PATH" |
| Video unavailable | Video may be private, age-restricted, or geo-blocked |
| MP4 is .webm | ffmpeg merges to mp4 automatically — check your player |

---

*Softcurse © 2025 — Built with Python, tkinter, yt-dlp, ffmpeg*
