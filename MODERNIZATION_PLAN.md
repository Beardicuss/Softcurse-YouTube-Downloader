# Softcurse Media Downloader Modernization Plan

## Goal

Modernize and harden the existing Windows application first, then build an Android version in a separate project folder without destabilizing the desktop release.

The work is intentionally divided into milestones. Each milestone should leave the application in a working, testable state.

## Current progress

- Phase 0 baseline and safety net: complete.
- Phase 1 download engine correctness: complete; live-media smoke testing remains part of release validation.
- Phase 2 persistence and network hardening: complete.
- Phase 3 Windows architecture modernization: complete at the service boundary; UI component extraction continues as part of the UX refresh.
- Phase 4 Windows UX refresh: complete; accessibility, focus navigation,
  reduced motion, DPI handling, error presentation, the sequential download queue,
  history filtering, responsive polish, and first-run diagnostics are complete.
- Phase 5 packaging, updates, and Windows release: complete for unsigned release
  candidates; code signing and clean-machine acceptance remain release-operator steps.
- Windows clean-machine acceptance testing: postponed at the user's request.
- Android Phase A decision gate: complete for the initial GitHub-distributed,
  on-device proof-of-concept direction.
- Android Phase B foundation: complete; the Compose shell, responsive navigation,
  shared HEX theme, URL validation, Room queue/history, DataStore settings,
  foreground WorkManager simulation, unit tests, CI, and debug build are complete.
- Android Phase B emulator validation: complete on Android 16/API 36 at phone and
  tablet widths; cold launch, simulated work, history persistence, and responsive
  navigation passed without runtime crashes.
- Android Phase C proof-of-concept code: implemented behind an opt-in setting using
  bundled yt-dlp and non-GPL FFmpeg. ARM64 installation, foreground execution,
  real MP4 download, MP3 conversion, MediaStore export, and failed-download cleanup
  pass on an Android 11 Redmi Note 8 Pro; cancellation and lifecycle stress gates remain.
- Android scoped-storage export: implemented for Android 10+ through MediaStore;
  Android 8–9 deliberately retain app-specific output without broad storage access.
- Android visual identity pass: in progress; the installed application and APK now use
  the Softcurse Systems Media Downloader name and established MP3/MP4 logo. The Compose
  shell includes an animated motherboard/neural circuit background: red while idle and
  sequentially green while queue work is pending or running, with a static reduced-motion mode.
- Cancellation, process-death, network-loss/retry, storage-exhaustion, Wi-Fi-only,
  thermal, battery, and MP3/MP4 playback testing have passed on connected ARM64 hardware.
  In-app release identity, privacy, permission disclosure, responsible-use guidance, and
  third-party/license presentation are implemented and validated on ARM64 hardware. Next:
  configure signed release APK/AAB, shrinking rules, and reproducible CI artifacts.

## Guiding principles

- Preserve the current working behavior while replacing fragile internals incrementally.
- Fix correctness and data-safety issues before visual redesigns or new features.
- Keep the download engine independent from Tkinter so it can be tested without launching the GUI.
- Treat Windows and Android as separate applications with shared product behavior, not as one mixed codebase.
- Do not reuse desktop-only implementation details on Android unless they are demonstrably maintainable there.
- Respect platform terms, copyright, and distribution-store rules when selecting Android download capabilities.

## Proposed repository layout

The current files can remain at the repository root during Windows stabilization. After the Windows architecture has been cleaned up, move toward:

```text
softcurse-media-downloader/
|-- windows/                 # Existing Python/Tkinter application
|   |-- src/
|   |-- tests/
|   |-- assets/
|   |-- installer/
|   `-- pyproject.toml
|-- android/                 # Separate Android Studio project
|   |-- app/
|   |-- build.gradle.kts
|   `-- settings.gradle.kts
|-- docs/
|-- README.md
`-- LICENSE
```

Do not perform this directory migration at the start. It would create noisy path and packaging changes while core bugs are still being fixed.

---

## Phase 0 - Baseline and safety net

### Work

- Record supported Windows and Python versions.
- Add a small set of owned/public test URLs for opt-in manual smoke testing.
- Add unit-test configuration and coverage reporting.
- Add Ruff configuration and establish a manageable lint baseline.
- Add GitHub Actions for compilation, unit tests, and linting.
- Document the current MP3, MP4, playlist, trim, metadata, player, history, and tray flows.
- Create a manual release checklist for source and packaged builds.

### Exit criteria

- Existing behavior is reproducible.
- Tests and static checks run with one documented command.
- Pull requests cannot silently break compilation or unit tests.

---

## Phase 1 - Download engine correctness

### Work

1. Replace the shared cancellation Boolean with a per-job cancellation event and job ID.
2. Prevent a new job from starting until the previous worker has exited.
3. Ignore callbacks from jobs that are no longer current.
4. Track successful and failed playlist entries separately.
5. Report partial playlist completion accurately and fail when no entry succeeds.
6. Capture actual final output paths from yt-dlp hooks.
7. Apply metadata only to files created by the current job.
8. Validate download mode, quality, output directory, filename template, and URL before starting.
9. Strictly validate clip timestamps and require the end to be later than the start.
10. Introduce typed result objects for progress, completion, errors, and downloaded files.

### Tests

- Successful and failed single downloads.
- Mixed-success and all-failed playlists.
- Cancellation before extraction, during transfer, and during playlist processing.
- A cancelled job followed by a new job.
- Valid and invalid clip ranges.
- Unknown formats and qualities.
- Metadata targeting only newly created files.

### Exit criteria

- The UI never records a failed download as successful.
- Cancelling or restarting cannot mix two jobs' callbacks.
- Existing destination files are never modified unintentionally.

---

## Phase 2 - Persistence and network hardening

### Work

- Validate and migrate configuration through an explicit schema version.
- Store configuration and history in the Windows application-data directory instead of the user's home directory.
- Write JSON atomically through a temporary file and replace operation.
- Preserve and report malformed configuration/history rather than silently discarding it.
- Add bounded network response sizes and stricter URL handling for thumbnails.
- Add request IDs to thumbnail lookups so stale responses are discarded.
- Improve SponsorBlock video-ID parsing, range normalization, and overlap handling.
- Add retry/backoff only where it improves transient network failures.
- Replace broad exception suppression with useful diagnostics and structured logs.

### Exit criteria

- Settings can evolve without breaking older installations.
- Interrupted writes cannot corrupt configuration or history.
- Old thumbnail requests cannot overwrite the active preview.

---

## Phase 3 - Windows architecture modernization

### Work

- Introduce a `src` package and separate application layers:
  - domain models and validation;
  - download service;
  - persistence repositories;
  - platform integrations;
  - Tkinter views/controllers.
- Split the large `gui.py` into screen or component modules.
- Centralize application version and resource-path resolution.
- Replace ad-hoc callback dictionaries with typed dataclasses or enums.
- Add dependency injection at the controller boundary so UI behavior can be tested.
- Move optional-dependency installation out of normal UI logic.
- Adopt `pyproject.toml` for metadata, dependencies, test, and lint configuration.

### Exit criteria

- Core download orchestration can be tested without Tkinter.
- No single UI module owns the entire application.
- Version, paths, and packaging metadata have one source of truth.

---

## Phase 4 - Windows UX refresh

### Work

- Preserve the Softcurse identity while simplifying dense CRT/glitch effects.
- Add a real multi-URL download queue with per-item status and cancellation.
- Improve keyboard navigation, focus visibility, contrast, scaling, and screen-reader labels.
- Make high-DPI behavior and responsive resizing predictable.
- Add a first-run dependency and FFmpeg diagnostic screen.
- Add clear error categories with actionable recovery steps.
- Improve history with search, filtering, retry, and reveal/play actions.
- Add theme options: modern dark, Softcurse cyberpunk, and reduced-motion mode.
- Make progress reporting consistent across extraction, downloading, merging, conversion, and tagging.

### Exit criteria

- All primary workflows work at common Windows scaling levels.
- The application is usable without animation and primarily by keyboard.
- Queue state and errors are understandable without reading raw yt-dlp output.

---

## Phase 5 - Packaging, updates, and Windows release

### Work

- Lock direct and transitive dependency versions for release builds.
- Build in a clean CI environment instead of relying on ambient packages.
- Verify bundled FFmpeg discovery and licensing documentation.
- Remove in-app `pip install` and `pip upgrade` behavior from frozen builds.
- Select an application-level update mechanism with signed release artifacts.
- Add executable metadata, icons, version information, and uninstall cleanup rules.
- Produce SHA-256 checksums and a release changelog.
- Test source, portable executable, and installer variants on clean Windows systems.
- Sign the executable and installer when a suitable certificate is available.

### Exit criteria

- A clean machine can install, launch, download, update, and uninstall the application.
- Builds are reproducible from documented inputs.
- Release artifacts have version information and checksums.

---

## Phase 6 - Optional Windows feature upgrades

Only begin these after the stable release milestone:

- Download queue persistence and restart recovery.
- Subtitle and thumbnail download options.
- Cookie/browser-session configuration with explicit privacy messaging.
- Audio normalization and ReplayGain support.
- Presets for common format/quality combinations.
- Duplicate-file policy and collision previews.
- Import/export of settings and history.
- Diagnostic bundle export with sensitive values removed.

---

# Android application plan

## Phase A - Product and technical decision gate

Create the Android application only after Phase 5 is stable. Before implementation, decide:

1. Whether media extraction occurs fully on-device or through a service controlled by the project.
2. Which sources and download behaviors can be distributed under their terms and the intended app-store rules.
3. How FFmpeg functionality will be provided and what licensing obligations apply.
4. Whether the Android release is intended for Google Play, direct APK distribution, or both.

Recommended starting point: a native Kotlin application using Jetpack Compose, with WorkManager for long-running jobs, Room for history, DataStore for settings, and Media3 for playback. Keep extraction behind an interface so the implementation can change without rewriting the UI.

Do not assume the Python desktop engine can simply be copied into an Android app. Python runtimes, yt-dlp integration, FFmpeg packaging, background execution, storage permissions, battery policies, and store review rules all require a separate design decision.

## Phase B - Android foundation

### Work

- Create `android/` as an independent Android Studio project.
- Set up Kotlin, Jetpack Compose, Material 3, navigation, dependency injection, and automated tests.
- Define shared product concepts independently in Kotlin: download request, format preset, progress, result, history entry, and application settings.
- Implement URL intake, validation, format selection, destination selection, and a mocked download queue.
- Implement Room history and DataStore preferences.
- Establish notification channels and foreground-worker behavior.

### Exit criteria

- The Android UI and queue workflow function using a fake engine.
- Configuration and history survive restarts.
- Background-job behavior is testable before real extraction is connected.

## Phase C - Android download engine proof of concept

### Work

- Prototype the chosen extraction approach behind the engine interface.
- Test MP3 and MP4 paths on several Android API levels and device architectures.
- Verify network loss and resume behavior. Network loss now produces an actionable failure,
  cleans partial files, and supports same-record retry without duplicate output; Wi-Fi-only
  work remains pending on cellular and starts when Wi-Fi returns. Reliable cancellation, process-death recovery,
  and storage-exhaustion handling have passed physical ARM64 validation, including
  stable-ID restart, Room/WorkManager reconciliation, capacity gates, scoped cleanup,
  and protection against late native callbacks.
- Android 13+ notification permission grant, denial, retry, cold-restart persistence,
  and foreground progress display passed on the API 36 emulator.
- Validate FFmpeg performance, thermal impact, battery use, and binary size. ARM64 thermal
  and battery sampling passed with thermal status 0; the current debug APK is about 66.9 MB.
- Implement scoped-storage output through Android-supported APIs.
- Add clear error handling for unsupported or restricted media.

### Exit criteria

- The proof of concept works on real devices, not only an emulator.
- Licensing and distribution implications are documented and accepted.
- Background downloads survive normal Android lifecycle events safely.

## Phase D - Android feature completion

### Work

- Connect the real engine to the Compose UI.
- Add per-item progress, cancellation, retry, and notifications.
- Add history, share/open actions, and Media3 playback.
- Add metadata and trim support only after the basic pipeline is reliable.
- Adapt the Softcurse visual design to mobile accessibility and touch targets.
- Add phone/tablet layouts, dark theme, dynamic color opt-out, and reduced motion.
- Add unit, integration, and device tests.

## Phase E - Android release

### Work

- Perform privacy, security, licensing, and store-policy review.
- Add a privacy policy and in-app disclosure for network services and local files.
- Minimize permissions and document every requested permission.
- Configure signing, release builds, obfuscation rules, crash reporting choice, and reproducible CI builds.
- Run internal testing, closed testing, and staged rollout as applicable.

---

## Suggested issue/branch sequence

1. `test/baseline-ci`
2. `fix/job-lifecycle`
3. `fix/playlist-accounting`
4. `fix/metadata-targeting`
5. `fix/input-validation`
6. `fix/persistence-and-preview-races`
7. `refactor/application-layers`
8. `refactor/gui-components`
9. `feat/download-queue`
10. `feat/windows-ux-refresh`
11. `build/reproducible-windows-release`
12. `feat/android-foundation`

Keep each change reviewable and add regression tests with every correctness fix.

## Definition of done for the overall program

### Windows

- Correct cancellation and playlist accounting.
- No unintended metadata changes.
- Automated tests and CI cover the main engine paths.
- Accessible, DPI-aware refreshed interface.
- Clean, versioned, reproducible installer and update story.

### Android

- Independent `android/` project with a native mobile lifecycle.
- Verified extraction/conversion approach with documented licensing and distribution constraints.
- Reliable foreground/background queue, scoped storage, history, and playback.
- Tested signed release suitable for the selected distribution channel.
