# Windows release checklist

## Automated checks

- [ ] Install from `requirements-dev.txt` in a clean environment.
- [ ] Run `.\verify.ps1` successfully.
- [ ] Confirm `python -m pip check` reports no broken requirements.

## Functional checks

- [ ] Complete the manual smoke test in `docs/TESTING.md`.
- [ ] Test MP3 and MP4 output on a clean Windows 10 or 11 system.
- [ ] Test cancellation, playlist partial failure, and invalid input handling.
- [ ] Confirm metadata changes affect only the intended downloaded files.
- [ ] Verify history, settings, notifications, tray behavior, and the mini player.

## Packaging checks

- [ ] Build the executable from a clean environment.
- [ ] Install exactly `requirements-lock.txt` with `--require-hashes`.
- [ ] Confirm UI, executable metadata, installer, and `pyproject.toml` match `VERSION`.
- [ ] Confirm bundled or system FFmpeg discovery.
- [ ] Install, launch, upgrade, and uninstall through the installer.
- [ ] Confirm version metadata is consistent in the app, installer, and README.
- [ ] Scan the packaged artifacts with the chosen security tooling.
- [ ] Generate and publish SHA-256 checksums.
- [ ] Run `installer/build_installer.ps1` and retain its installer checksum.
- [ ] Run the packaged executable on a clean Windows test machine before signing.
- [ ] Sign the executable and installer when a signing certificate is available.
- [ ] Prepare release notes covering user-visible changes and known limitations.
