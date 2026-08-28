# Security Best-Practices Audit

Audit date: 2026-08-28  
Scope: Python source, packaging scripts, installer, declared dependencies, and local release layout.

## Executive summary

No critical vulnerability, embedded credential, shell injection, or known vulnerable declared dependency was found. The application is a local desktop client, which reduces the impact of server-style issues, but it processes attacker-controlled URLs, metadata, filenames, images, and media through several large parsers. The most important hardening work is to constrain output paths, bound thumbnail processing, remove in-app package installation, and make releases reproducible and signed.

Automated evidence: `pip-audit -r requirements.txt` found no known vulnerabilities; Bandit found only low-severity subprocess and swallowed-exception warnings; the subprocess calls use argument arrays and do not enable `shell=True`. A repository secret-pattern scan found no credential-like assignments.

## High severity

No confirmed high-severity finding.

## Medium severity

### SEC-001 — Filename templates can escape the selected output directory

- Location: `downloader.py:226-227` (template is joined directly into `outtmpl`); source is persisted configuration at `config.py:15,27`.
- Impact: a modified configuration can use absolute paths or `..` components and cause downloaded files to be written outside the folder selected in the UI, potentially overwriting user files where yt-dlp permits it.
- Recommendation: validate templates as relative names, reject absolute paths and parent traversal, and verify the resolved yt-dlp output remains under the resolved output directory.

### SEC-002 — Thumbnail download is unbounded and feeds untrusted bytes to an image parser

- Location: `thumbnail.py:107-115`.
- Impact: a crafted extractor result can make the client consume excessive memory or CPU through a very large response or decompression-bomb image. This is a local denial of service and expands exposure to image-decoder vulnerabilities.
- Recommendation: allow HTTPS only, cap response bytes (for example 10 MiB), check content type, set Pillow pixel limits deliberately, and reject truncated/oversized images before creating Tk objects.

### SEC-003 — In-app dependency installation executes mutable third-party packages

- Locations: `downloader.py:38-62`, `thumbnail.py:23-35`, `metadata_editor.py:43-56`, `player.py:43-58`, `tray.py:32-55`.
- Impact: clicking install/update downloads and executes the latest package and transitive dependencies without hashes or a lock file. A compromised package index/account or malicious network configuration would become code execution as the user. In a frozen build, `sys.executable -m pip` is also generally nonfunctional.
- Recommendation: ship reviewed dependencies in signed releases; remove runtime installation from production builds; use a lock file with hashes for builds.

### SEC-004 — FFmpeg discovery trusts writable locations and `PATH`

- Location: `downloader.py:10-28`.
- Impact: a malicious `ffmpeg.exe` placed beside the program, in its parent directory, or earlier on `PATH` can be executed. This is mainly a local binary-hijacking risk.
- Recommendation: ship FFmpeg in one fixed application-owned directory, do not search the parent directory, resolve the system binary with `shutil.which`, and document/check the expected release hash.

## Low severity

### SEC-005 — URL validation is only a string-prefix check

- Location: `gui.py:1305-1311`.
- Risk: strings beginning with `http` are accepted without parsing scheme/host. yt-dlp handles most invalid input safely, but this increases exposure to local-network targets through generic extractors.
- Recommendation: parse with `urllib.parse.urlsplit`, allow only `http`/`https`, require a hostname, and optionally warn before accessing loopback/private/link-local addresses.

### SEC-006 — Download history stores complete URLs and local paths in plaintext

- Locations: `history.py:10,24-61`.
- Risk: URLs may contain private/unlisted IDs, query tokens, or personal content, and output paths reveal usernames/directory structure to other processes with profile access.
- Recommendation: strip sensitive query parameters, offer history disable/clear controls, use the platform app-data directory, and create the file with user-only permissions where supported.

### SEC-007 — Release integrity is not established

- Locations: `build_exe.bat:14-31`, `Softcurse_Media_Downloader.spec:19-38`, `installer/softcurse_installer.iss:20-60`.
- Risk: builds are not reproducible, checksummed, or code-signed; users cannot distinguish an authentic binary from a modified one. UPX packing can also increase antivirus false positives.
- Recommendation: pin the build environment, publish SHA-256 checksums/SBOM, disable UPX unless required, and Authenticode-sign both executable and installer.

### SEC-008 — Broad exception suppression hides integrity and security-relevant failures

- Examples: `config.py:23-29`, `history.py:14-21`, `sponsorblock.py:99-104`, `thumbnail.py:122-128`.
- Risk: corrupted state and network/parser failures silently fall back, preventing diagnosis and making tampering indistinguishable from normal absence.
- Recommendation: catch expected exception types and log sanitized diagnostics; preserve corrupt files for recovery rather than silently replacing state.

## Positive controls observed

- No `shell=True`, `eval`, `exec`, pickle, or unsafe YAML loading was found.
- External processes receive argument arrays rather than interpolated shell commands.
- SponsorBlock uses HTTPS and a hashed-prefix lookup.
- Config/history JSON parsing does not instantiate arbitrary objects.
- Current declared dependencies had no known advisories in the audit snapshot.

## Remediation priority

1. Validate output templates and bound thumbnail downloads.
2. Replace runtime dependency installation with locked, bundled release dependencies.
3. Restrict and verify FFmpeg discovery.
4. Add CI for tests, Ruff/Bandit, dependency audit, secret scanning, and signed reproducible releases.

