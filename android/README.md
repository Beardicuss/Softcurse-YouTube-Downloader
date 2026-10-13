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
- Opt-in on-device yt-dlp/FFmpeg proof of concept for ARM64 and x86_64
- Download-engine interface ready for a proof of concept
- Unit tests for URL validation

The safe default worker simulates progress. Settings contains an explicitly experimental
on-device engine using bundled yt-dlp and FFmpeg. It must pass the promotion gate documented in
`docs/ANDROID_ENGINE_POC.md` on real devices before becoming the default.

## Build

Set `ANDROID_SDK_ROOT` or create `local.properties` with an `sdk.dir` entry, then run:

```powershell
.\gradlew.bat testDebugUnitTest assembleDebug
```

The local development SDK used by this repository is API 36.

## Initial flow

```text
Download -> validate link -> persist request -> foreground simulated worker -> Queue
Queue -> progress or cancel -> persisted History
Settings -> persisted download preferences
Player -> foundation placeholder
```

On phones the primary destinations use bottom navigation. On tablets and wide windows the
same destinations move to a navigation rail.
