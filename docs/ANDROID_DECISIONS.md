# Android architecture decisions

## Distribution

The first Android proof of concept targets direct APK distribution through GitHub rather
than Google Play. Store distribution remains a later decision after the extraction engine,
FFmpeg licensing, permissions, and platform-policy implications have been reviewed.

## Technology

- Native Kotlin application.
- Jetpack Compose UI with responsive phone/tablet navigation.
- Minimum Android API 26; compile and target API 36.
- Gradle wrapper committed with the project.
- Softcurse HEX colors are centralized in the Compose theme.

## Download engine boundary

The UI depends on a Kotlin `DownloadEngine` interface. Phase B uses a fake engine and an
in-memory queue. An on-device implementation is the preferred Phase C experiment, but it
must not be coupled to screens until cancellation, process death, storage, FFmpeg packaging,
licensing, and real-device behavior have been validated.

The desktop Python engine is not copied into the Android application.

## Playback behavior

Downloaded media must never begin playing automatically. Only completed records with a
persisted MediaStore URI are offered to the player. Selecting a record, moving to the
previous/next record, or opening the Player prepares media silently; playback requires an
explicit press of Play. Leaving the Player releases playback. The initial implementation
uses the platform `VideoView`/`MediaPlayer` lifecycle so both audio and video can be proven
on hardware without another runtime dependency; Media3 remains a later upgrade if richer
session, background playback, or codec behavior is required.

## Deferred Windows work

Clean-machine Windows installer acceptance testing is intentionally postponed at the user's
request. It remains a release checklist item and is not treated as completed.
