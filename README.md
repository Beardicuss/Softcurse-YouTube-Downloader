<p align="center">
  <img src="assets/yt.png" alt="Softcurse Media Downloader" width="200">
</p>

<h1 align="center">Softcurse Media Downloader</h1>

<p align="center">
  <strong>Multi-platform media downloader with a cyberpunk-themed desktop interface.</strong>
</p>

<p align="center">
  <a href="https://softcurse-website.pages.dev/"><img src="https://img.shields.io/badge/website-softcurse.dev-00FFFF?style=flat-square&logo=googlechrome&logoColor=white&labelColor=020202" alt="Website"></a>
  <img src="https://img.shields.io/badge/version-1.0-00FFFF?style=flat-square&labelColor=020202" alt="Version 1.0">
  <img src="https://img.shields.io/badge/python-3.10+-00FFFF?style=flat-square&logo=python&logoColor=white&labelColor=020202" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/platform-Windows-00FFFF?style=flat-square&logo=windows&logoColor=white&labelColor=020202" alt="Windows">
  <img src="https://img.shields.io/badge/license-MIT-00FFFF?style=flat-square&labelColor=020202" alt="MIT License">
  <img src="https://img.shields.io/badge/UI-tkinter-FF00FF?style=flat-square&labelColor=020202" alt="Tkinter">
</p>

---

## Table of Contents

- [Overview](#overview)
- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Architecture](#%EF%B8%8F-architecture)
- [Build Standalone EXE](#-build-standalone-exe)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [Roadmap](#%EF%B8%8F-roadmap)
- [License](#-license)
- [Acknowledgements](#-acknowledgements)

---

## Overview

**Softcurse Media Downloader** is a desktop application that downloads audio and video from YouTube, Instagram, TikTok, and X. It converts media to MP3 or MP4 with configurable quality settings, all wrapped in a SOFTCURSE/SYS cyberpunk-themed interface with neon accents, CRT scanline effects, and glitch animations.

Built for users who want a fast, offline-capable media downloader without browser extensions or web-based tools.

---

## ✨ Features

- 🎵 **MP3 Mode** — download audio with quality from 128–320 kbps
- 🎬 **MP4 Mode** — download video at best / 1080p / 720p / 480p / 360p
- 🌐 **Multi-Platform** — YouTube, Instagram, TikTok, and X
- 📋 **Playlist Support** — batch-download entire YouTube playlists
- 🗂️ **Download Queue** — paste multiple URLs and process them sequentially
- 🎵 **FLAC / WAV Export** — lossless audio output options
- 🛡️ **SponsorBlock** — auto-skip sponsors, intros, and outros
- 🏷️ **Metadata Editor** — set artist, album, genre, year, and track tags
- 🎧 **Built-in Mini Player** — waveform visualizer with playlist management
- 🖼️ **Thumbnail Preview** — see the thumbnail before downloading
- ✂️ **Clip / Trim** — extract segments by timestamp
- 📜 **Download History** — track, retry, and manage past downloads
- 🔎 **History Search** — filter by title, URL, format, status, or folder
- 🔔 **System Tray** — minimize to tray with desktop notifications
- 📁 **Filename Templates** — customize output filenames
- 📺 **CRT Scanlines** — retro visual effects with toggle
- 📊 **Real-Time Progress** — neon progress bar with speed and ETA
- ♿ **Accessible Motion & Keyboard Controls** — reduced-motion mode, visible focus,
  and shortcuts for primary navigation
- 🩺 **System Readiness Check** — verifies required and optional components without
  silently modifying the installation

---

## 📦 Installation

### Prerequisites

- **Python 3.10+** — [python.org](https://python.org) (check *Add Python to PATH*)
- **ffmpeg** — required for audio conversion and video merging

### Step 1 — Install ffmpeg

```bash
winget install ffmpeg
```

Or download from [ffmpeg.org](https://ffmpeg.org) and place `ffmpeg.exe` in the `ffmpeg/` folder.

### Step 2 — Install dependencies

```bash
setup.bat
```

This installs `yt-dlp`, `Pillow`, `pystray`, and `plyer` automatically.

### Step 3 — Launch

```bash
launch.bat
```

Or run directly:

```bash
python main.py
```

---

## 🚀 Quick Start

1. Launch the app with `launch.bat` or `python main.py`
2. Paste a supported URL (YouTube, Instagram, TikTok, X)
3. Choose an output folder
4. Select the **MP3** or **MP4** tab
5. Pick your quality setting
6. Click **[ ♪ DOWNLOAD MP3 ]** or **[ ▶ DOWNLOAD MP4 ]**

The download progress is shown with a neon progress bar, speed indicator, and ETA.

---

## 🔧 Configuration

Settings and history are stored under `%LOCALAPPDATA%\Softcurse Media Downloader`.
Older `.softcurse_config.json` and `.softcurse_history.json` files in the user home
folder are imported automatically on first launch. Malformed JSON files are preserved
with a timestamped `.corrupt-*` suffix so they can be inspected or recovered.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `output_folder` | string | User Music folder | Audio output directory |
| `mp4_output_folder` | string | User Videos folder | Video output directory |
| `quality` | string | `"320"` | MP3 quality preset |
| `video_quality` | string | `"best"` | Video quality preset |
| `audio_format` | string | `"mp3"` | Default audio format |
| `filename_template` | string | `"%(title)s"` | yt-dlp filename template |
| `minimize_to_tray` | bool | `false` | Keep the application in the tray on close |
| `notify_on_complete` | bool | `true` | Show completion and failure notifications |
| `crt_effects` | bool | `true` | CRT scanline visual effects |
| `reduced_motion` | bool | `false` | Disable glitch, pulse, and scanline animations |
| `sponsorblock` | bool | `false` | SponsorBlock segment skipping |
| `sb_categories` | list | `["sponsor","intro","outro","selfpromo","interaction"]` | SponsorBlock categories |

Optional dependencies are installed on demand from the Settings tab:

| Package | Feature |
|---------|---------|
| `mutagen` | Metadata tag editing |
| `pygame` | Built-in audio player |

Keyboard shortcuts are documented in [Windows interaction flow](docs/UX_FLOW.md).
Packaged builds are updated or repaired as a complete application; the frozen
executable does not attempt to modify its bundled Python packages with `pip`.

---

## 🏗️ Architecture

```
Softcurse Media Downloader/
├── main.py              ← Entry point
├── app_info.py          ← Application identity and packaged resource paths
├── gui.py               ← SOFTCURSE/SYS UI (tkinter, CRT effects, glitch)
├── downloader.py        ← yt-dlp + ffmpeg engine (MP3, MP4, FLAC, WAV)
├── download_models.py   ← Typed download requests, progress, and results
├── config.py            ← Settings persistence (.json)
├── storage.py           ← Atomic application-data persistence
├── diagnostics.py       ← Rotating application logs
├── history.py           ← Download history manager
├── player.py            ← Built-in mini player (pygame + waveform)
├── metadata_editor.py   ← ID3 / FLAC / MP4 / OGG tag editor (mutagen)
├── thumbnail.py         ← Thumbnail fetching and display
├── sponsorblock.py      ← SponsorBlock API integration
├── tray.py              ← System tray icon (pystray + plyer notifications)
├── preview_controller.py← Stale asynchronous preview protection
├── ui_theme.py          ← Desktop design tokens
├── requirements.txt     ← Core dependencies
├── setup.bat            ← Dependency installer
├── launch.bat           ← App launcher
├── build_exe.bat        ← PyInstaller build script
├── assets/              ← Icons and images
├── ffmpeg/              ← Optional bundled ffmpeg.exe
└── installer/           ← Inno Setup installer script
```

---

## 📦 Build Standalone EXE

To distribute without requiring Python:

1. Place `ffmpeg.exe` in the `ffmpeg/` folder
2. Run `build_exe.bat` (uses the hash-locked `requirements-lock.txt`)
3. Find `Softcurse_Media_Downloader.exe` in the `dist/` folder

To build a Windows installer:

1. Install [Inno Setup 6 or 7](https://jrsoftware.org/isdl.php)
2. Run `installer/build_installer.ps1`
3. Find the versioned installer and SHA-256 checksum in `installer/Output/`

---

## 🔍 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ffmpeg not found` | `winget install ffmpeg` or place `ffmpeg.exe` in `./ffmpeg/` |
| `yt-dlp not found` | `pip install yt-dlp` or run `setup.bat` |
| Python not found | Install from [python.org](https://python.org), check "Add to PATH" |
| Video unavailable | Video may be private, age-restricted, or geo-blocked |
| MP4 exports as .webm | ffmpeg merges to MP4 automatically — update your media player |
| No audio in player | Install `pygame` from the Settings tab |
| Tags not saving | Install `mutagen` from the Settings tab |

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](.github/CONTRIBUTING.md) for details on the development workflow, coding standards, and how to submit pull requests.

For local verification, install `requirements-dev.txt` and run:

```powershell
.\verify.ps1
```

See [Testing and verification](docs/TESTING.md) for the manual smoke test and
[Windows release checklist](docs/RELEASE_CHECKLIST.md) for release validation.

See our [Code of Conduct](.github/CODE_OF_CONDUCT.md) for community standards.

---

## 🛣️ Roadmap

- [ ] Batch URL queue (paste multiple links at once)
- [ ] Drag-and-drop URL support
- [ ] Audio normalization (ReplayGain / loudness targeting)
- [ ] Scheduled downloads
- [ ] Plugin system for additional platform extractors
- [ ] Linux and macOS support

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

You are free to use, modify, and distribute this software with attribution.

---

## 👥 Acknowledgements

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — the media extraction engine
- [ffmpeg](https://ffmpeg.org) — audio/video processing
- [Pillow](https://python-pillow.org) — image handling
- [pygame](https://www.pygame.org) — audio playback
- [mutagen](https://mutagen.readthedocs.io) — metadata tagging
- [pystray](https://github.com/moses-palmer/pystray) — system tray integration
- [plyer](https://github.com/kivy/plyer) — desktop notifications

---

<p align="center">
  <sub><a href="https://softcurse-website.pages.dev/">Softcurse Systems</a> © 2025 — Built with Python, tkinter, yt-dlp, and ffmpeg</sub>
</p>
