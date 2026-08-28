# Softcurse Media Downloader — Project Audit

Audit date: 2026-08-28

## Executive summary

The application has a clear module split and compiles successfully, but its download engine previously hid yt-dlp failures and then announced success. That directly explains the reported “only an image downloads” symptom: MP3 mode writes a thumbnail first, conversion/download fails, `ignoreerrors=True` suppresses the failure, and the UI records completion. This audit fixes that behavior and adds regression coverage.

The project is not yet release-grade. It has only two newly added engine tests, no CI, 137 Ruff findings, broad exception suppression, non-reproducible packaging, and several correctness races. The highest functional risks are false playlist success, cancellation races, folder-wide metadata mutation, and stale preview callbacks.

## Confirmed download defect and applied fix

### BUG-001 — Media failures were masked as successful image-only downloads (fixed)

- Root cause: `downloader.py` used `writethumbnail=True` for MP3, `ignoreerrors=True`, `no_warnings=True`, and unconditionally invoked completion after `ydl.download()`.
- Fix: warnings/errors are forwarded to the UI, `ignoreerrors` is disabled, and nonzero yt-dlp results become errors. See `downloader.py:146-160`, `downloader.py:256-269`, and `downloader.py:326-335`.
- Regression tests: `test_downloader.py` verifies nonzero results cannot call completion and zero results do.
- Environment finding: the source environment initially had no `yt_dlp` module. Installing `requirements.txt` supplied yt-dlp 2026.08.19. FFmpeg is present and executable.

## Functional findings

### High priority

#### BUG-002 — Playlist completion count is false when entries fail

- Location: `downloader.py:301-325`.
- Each entry exception is logged as skipped, but completion still reports the original total. If every item fails, the playlist can still be recorded as successful.
- Fix: track succeeded/failed counts; call `on_error` if none succeed; report partial completion explicitly.

#### BUG-003 — Metadata edits every audio file already in the destination folder

- Locations: `downloader.py:323-335`, `metadata_editor.py:156-170`.
- A single download with custom tags calls `write_tags_to_folder`, overwriting tags on unrelated existing music. MP4 is excluded from the folder helper despite MP4 tag support elsewhere.
- Fix: capture yt-dlp's final filepath(s) using postprocessor hooks and tag only those files.

#### BUG-004 — Cancel followed quickly by a new download creates a race

- Locations: `downloader.py:100-133`, `downloader.py:230-232`, `gui.py:1362-1365`.
- Cancel is one shared boolean. The GUI re-enables Download immediately while the worker is alive; starting again resets the flag, allowing the old job to continue and mixing callbacks with the new job.
- Fix: give each job its own cancellation event/ID, keep controls disabled until its worker exits, and ignore callbacks from non-current job IDs.

### Medium priority

#### BUG-005 — Thumbnail callbacks can show stale data

- Locations: `gui.py:554-563`, `thumbnail.py:39-130`.
- Every URL launches a daemon thread, but callbacks are not correlated with the current URL. A slower old request can overwrite a newer preview.
- Fix: pass a request token/URL through callbacks and discard stale results.

#### BUG-006 — Invalid clip values silently become unexpected ranges

- Locations: `downloader.py:65-88`, `downloader.py:176-194`, `downloader.py:280-286`.
- Invalid text becomes blank/zero, seconds/minutes are not range-checked, and end-before-start is not rejected.
- Fix: validate format and bounds in the GUI and engine; require end greater than start.

#### BUG-007 — Unknown format values silently select MP4

- Location: `downloader.py:199-225`.
- Any mode not present in `AUDIO_MODES` enters the MP4 branch, hiding corrupt configuration/caller errors.
- Fix: explicitly require one of `mp3`, `flac`, `wav`, `mp4`.

#### BUG-008 — In-app updates do not reliably work in frozen builds

- Locations: `downloader.py:38-62` and equivalent optional installers; `Softcurse_Media_Downloader.spec:4-16`.
- A frozen executable is not a Python interpreter with pip, and bundled modules cannot normally be upgraded in place. The UI promises an update that can fail silently behind redirected output.
- Fix: update the whole signed application or maintain a separately managed yt-dlp executable; do not invoke pip from the frozen GUI.

#### BUILD-001 — Packaging previously did not install project dependencies

- Location: `build_exe.bat:14-31`.
- The build installed only PyInstaller, so release contents depended on ambient packages. The script now installs/upgrades `requirements.txt` and aborts on installation/build failure. A lock file is still needed for reproducibility.

### Low priority / maintainability

#### QA-001 — No established test or CI pipeline

- Only `test_downloader.py` now exists; `.github` contains templates but no workflows.
- Add unit tests for format options, clips, playlists, cancellation, output paths, metadata targeting, config corruption, and SponsorBlock range inversion. Add one opt-in live extractor smoke test.

#### QA-002 — Static analysis baseline is noisy

- Ruff reports 137 findings: unused imports/variables, bare and broad exceptions, modern typing issues, unsorted imports, and style/complexity warnings.
- Important examples: unused `downloaded_files` in `downloader.py`, bare `except` in `gui.py:1281-1285`, unused GUI imports/variables, and numerous swallowed player/tray failures.
- Fix correctness-related warnings first; avoid bulk auto-fixing UI code without visual regression checks.

#### BUILD-002 — Resource paths depend on current working directory

- Location: `gui.py:106-107`; packaging files place or reference the icon differently.
- Launching outside the repository can lose the icon. Use one resource resolver based on `sys._MEIPASS`/executable directory and package assets consistently.

#### DOC-001 — Configuration documentation does not match implementation

- README documents generic keys such as `format` and `playlist_mode`, while `config.py` uses `audio_format` and the GUI playlist state is not persisted there.
- Update the configuration table from the actual schema.

## Verification performed

- `python -m compileall -q .` — passed.
- `python -m unittest -v` — 2/2 passed.
- `python -m pip check` — passed.
- `python -m pip_audit -r requirements.txt` — no known vulnerabilities.
- Secret-pattern scan — no findings.
- FFmpeg executable check — passed (build dated 2026-07-24).
- Live failure-path probe — unavailable YouTube test media correctly called the error callback and never completion.
- Ruff — 137 findings (baseline documented above).
- Bandit — low-severity warnings only; console report encountered Windows CP1252 output failure after emitting findings.

## Recommended execution order

1. Rebuild the executable with the updated yt-dlp and confirm one owned/public MP3 and MP4 URL end to end.
2. Fix playlist accounting, job cancellation isolation, and metadata targeting.
3. Add output-path and thumbnail hardening from the security report.
4. Establish locked dependencies and CI, then reduce the Ruff baseline.
5. Produce a signed installer and publish hashes.

