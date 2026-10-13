# Android on-device engine proof of concept

## Status

The proof-of-concept implementation compiles and is available behind the disabled-by-default
`Experimental on-device engine` setting. The normal path continues to use the simulated worker.

The experimental worker:

1. Runs as foreground WorkManager work.
2. Uses `dev.ffmpegkit-maintained:yt-dlp-android:2.0.2` for extraction.
3. Downloads MP4 as a progressive MP4 stream where the source provides one.
4. Downloads the best available audio stream and converts it with
   `dev.ffmpegkit-maintained:ffmpeg-kit-audio:8.1.9` for MP3, FLAC, or WAV.
5. On Android 10+, exports completed output through MediaStore into public
   `Downloads/Softcurse` without broad storage permission.
6. On Android 8–9, retains output in the app-specific external directory rather than asking for
   legacy broad storage access.
7. Stores progress, result state, error information, and output location in Room.

## Emulator validation

The safe simulated-engine path was validated on an Android 16/API 36 x86_64 emulator:

- cold installation and launch completed without an Android runtime crash;
- a valid HTTPS request completed and moved from the queue into History;
- completed history survived a forced app stop and cold restart;
- the phone layout used bottom navigation at 1080 x 2400;
- the tablet-width layout switched to a navigation rail at 1600 x 2560.

This does not promote the experimental engine. Native extraction, FFmpeg conversion,
notifications, cancellation, and ARM64 behavior still require the physical-device gate below.

## Physical-device validation

Validated on an ARM64 Redmi Note 8 Pro running Android 11/API 30:

- debug APK installation and cold launch passed without an app runtime crash;
- the bundled Python/yt-dlp runtime initialized and downloaded a public MP4 test clip;
- MP4 export through MediaStore created a playable file in `Download/Softcurse`;
- the bundled non-GPL FFmpeg artifact converted the same public clip to MP3;
- MP3 export through MediaStore created a file in `Download/Softcurse`;
- foreground WorkManager execution and its notification ran during both paths;
- a rejected HTTP source produced a failed history record and left no partial file;
- completed Room history survived APK replacement and cold app launches.

Real-device testing found and fixed an Android 10+ export defect: media-specific
collections reject `Download` as a primary directory for some media types. The exporter
now writes all requested formats through `MediaStore.Downloads`, matching the documented
`Download/Softcurse` destination. Failed and cancelled work also removes UUID-scoped
temporary files from the app-specific staging directory.

Reliable cancellation was subsequently validated with a 263 MB public Blender-hosted
MP4 source. The transfer was cancelled while yt-dlp reported 27 percent. The record
moved immediately from Queue to History as `Cancelled`, the UUID-scoped staging
directory was empty, `Download/Softcurse` contained no exported file, and no late
native callback changed the record back to `Running` or `Complete`.

Cancellation now marks Room first, interrupts the yt-dlp future, cancels the exact
FFmpeg session, guards progress/completion writes by the persisted running state, and
deletes an export if cancellation wins the final MediaStore race.

Process-death recovery was validated on the same physical device with a 632 MB public
Blender-hosted source. Android terminated the complete app process at 5 percent. After
a cold relaunch under a new PID, WorkManager restarted the same unique job and it
advanced from 0 to 51 percent using the original stable UUID. There was one staging
file for that UUID, no duplicate Room record, and no MediaStore output. Cancelling the
recovered attempt removed the partial file.

Workers now accept persisted `Pending` or `Running` state on a restarted attempt,
remove only their UUID-scoped stale staging files before retry, and retain guarded
progress/completion transitions. App startup also reconciles active Room records with
WorkManager and marks only genuinely terminal or missing work as failed.

Storage exhaustion was validated on physical hardware through a debug-build-only
capacity fault. With zero bytes reported, the worker failed before network/Python work,
History displayed an actionable request to free at least 512 MiB, the UUID staging
directory stayed empty, and `Download/Softcurse` stayed empty. The override was removed
after the test and cannot affect release builds.

Production storage guards now require working headroom before extraction, source-size
plus reserve before audio conversion, and source-size plus reserve before MediaStore
export. Native `ENOSPC`/disk-full failures are normalized to a useful message. Failure
cleanup remains scoped to the current UUID and any pending export it created; existing
downloads are never deleted.

Android 13+ notification permission was validated on the API 36 emulator. A fresh
install stayed quiet until the user opened Settings and selected `Authorize
notifications`. The system dialog used the full application name. Granting permission
immediately changed the in-app state to online, persisted across a cold process restart,
and displayed a silent foreground notification with title, progress text, progress bar,
and app icon during simulated work.

The denial path also passed: selecting `Don't allow` returned the app to its offline
state, kept the authorization action available for a later retry, and allowed foreground
work to complete without a crash while Android suppressed the notification. A second
request reopened the system prompt successfully.

## Distribution and licensing

- The selected yt-dlp Android wrapper is MIT licensed and embeds CPython 3.13 and yt-dlp.
- The selected non-GPL FFmpeg audio artifact is LGPL-3.0. Do not replace it with a `-gpl`
  variant without deliberately changing the application licensing and distribution plan.
- About & Legal now exposes the privacy disclosure, permission purposes, responsible-use terms,
  third-party inventory, and upstream license/source links in the app. Matching publishable
  privacy and third-party notice documents live in `docs/ANDROID_PRIVACY_POLICY.md` and
  `docs/ANDROID_THIRD_PARTY_NOTICES.md`.
- Users must download only media they own or have permission to save. Source terms and local law
  remain applicable.

This is an engineering record, not legal advice.

## Known limitations

- Only `arm64-v8a` and `x86_64` are supported by the embedded Python wrapper.
- The wrapper adds roughly 60–80 MB before FFmpeg and other application code.
- The free wrapper lacks TLS browser-fingerprint impersonation, so some sources may reject it.
- yt-dlp is bundled and can only be updated by updating the dependency and rebuilding the app.
- Cancellation of active Python extraction has passed physical ARM64 validation.
- Friendly filename metadata and playlists are not done. Failed transfers now expose a
  same-record retry action; network interruptions are normalized to an actionable message.
- MP4 proof-of-concept selection favors a progressive MP4 to avoid an unvalidated merge path.
- Android 13+ notification permission UX passed on API 36; the Android 11 foreground
  notification path also passed on physical hardware.
- Real-device thermal and battery sampling passed on ARM64 hardware. A public MP4 transfer
  and MP3/FFmpeg conversion completed on battery power with thermal status 0 throughout.
  Peak observed CPU temperature was about 48.3 C during conversion; battery remained about
  28 C and skin about 31-32 C. Battery level remained at 87 percent for the test window.
  MIUI's charge counter was too coarse for an isolated short-run drain calculation;
  batterystats attributed 12.9 mAh of direct CPU energy to the app for the charge session.
  Network loss and Wi-Fi-only constraints also passed on ARM64 hardware.

## Promotion gate

Do not make the experimental engine the default until all of these pass on physical hardware:

- MP3 and MP4 download using owned/public test media.
- Cancellation terminates work and leaves no partial output. **Passed on ARM64 hardware.**
- Network loss produces a useful failure and retry path. **Passed on ARM64 hardware:**
  connectivity was removed at 81% and again at 45%, partial files were cleaned, the error
  was normalized, Retry reused the same Room node without duplication, and the retried MP4
  completed and exported successfully.
- Wi-Fi-only work remains pending on cellular and starts after validated Wi-Fi returns.
  **Passed on ARM64 hardware.**
- MP4 download and MP3/FFmpeg conversion complete without thermal throttling or unsafe
  battery/skin temperatures. **Passed on ARM64 hardware.**
- Physical playback passed for exported MP3 and MP4 media. Opening or changing tracks
  prepares media without autoplay; Play, Pause, Stop, Previous, Next, seeking state, and
  rendered MP4 frames were validated. A control-tint defect found during the test was fixed.
- Process death does not corrupt Room state or duplicate output. **Passed on ARM64 hardware.**
- Storage exhaustion is reported without deleting existing media. **Passed on ARM64 hardware.**
- App restart reconciles unfinished WorkManager and Room records. **Passed on ARM64 hardware.**
- ARM64 APK installation, notification, and foreground execution are verified.
- Android 13+ notification grant, denial, retry, persistence, and foreground display are verified.
- License and third-party notice presentation is implemented. **Passed on ARM64 hardware.**
