# Softcurse Downloader for Android

This is the independent native Android application for Softcurse Media Downloader.
It does not embed or import the Windows Python/Tkinter implementation.

## Current milestone

Phase B foundation (`0.1.0`):

- Kotlin and Jetpack Compose
- API 26 minimum, API 36 target
- Compose BOM 2026.06.00 (API-36-compatible 1.11.x line)
- Responsive bottom navigation on phones and navigation rail on wider devices
- Shared Softcurse HEX color and typography tokens
- URL validation and MP3/FLAC/WAV/MP4 selection
- Room-backed queue and history with a versioned schema
- DataStore preferences for default format, Wi-Fi-only jobs and reduced motion
- Foreground WorkManager simulation with progress, cancellation and notifications
- Opt-in on-device yt-dlp/FFmpeg engine for ARM64 and x86_64 with runtime yt-dlp updates
- Selectable YouTube playlist discovery and per-entry queue/history records
- Unit tests for URL validation, persistence, playlist parsing, and worker failure handling

The safe default worker simulates progress. Settings contains an explicitly experimental
on-device engine using updateable yt-dlp and bundled FFmpeg. Its reliability gates and remaining
promotion work are documented in `docs/ANDROID_ENGINE_POC.md` and the repository modernization plan.

## Build

Set `ANDROID_SDK_ROOT` or create `local.properties` with an `sdk.dir` entry, then run:

```powershell
.\gradlew.bat testDebugUnitTest assembleDebug
```

The local development SDK used by this repository is API 36.

## Initial flow

```text
Download -> inspect link/playlist -> persist selected entries -> foreground worker -> Queue
Queue -> progress or cancel -> persisted History
Settings -> persisted download preferences
Player -> foundation placeholder
```

On phones the primary destinations use bottom navigation. On tablets and wide windows the
same destinations move to a navigation rail.

## Privacy and support

The application stores its queue, history, settings, and latest crash report locally. Support
messages and reviewed crash reports are sent only after the user taps Send in the native form.
Formspree relays those submissions to `softcursesystems@gmail.com`; media URLs and queue contents
are not included.
