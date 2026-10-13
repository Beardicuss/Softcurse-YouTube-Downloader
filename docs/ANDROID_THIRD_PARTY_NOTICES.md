# Android third-party notices

Softcurse Systems Media Downloader uses the following open-source software. The linked upstream
license texts and copyright notices control; this inventory is an engineering aid and is not
legal advice.

| Component | Use | License | Source and license |
| --- | --- | --- | --- |
| AndroidX, Jetpack Compose, and Material | UI, lifecycle, Room, DataStore, WorkManager | Apache License 2.0 | <https://source.android.com/docs/setup/about/licenses> |
| Kotlin | Language and coroutines runtime | Apache License 2.0 | <https://github.com/JetBrains/kotlin> |
| yt-dlp Android wrapper | Android extraction and embedded Python integration | MIT License | <https://github.com/yausername/youtubedl-android> |
| yt-dlp | Extraction and source download engine | The Unlicense | <https://github.com/yt-dlp/yt-dlp> |
| CPython | Embedded Python runtime | Python Software Foundation License 2.0 | <https://docs.python.org/3/license.html> |
| FFmpegKit maintained audio build | Android audio conversion package | LGPL v3 | <https://github.com/arthenica/ffmpeg-kit> |
| FFmpeg | Audio decoding and conversion | LGPL v2.1 or later | <https://ffmpeg.org/legal.html> |
| JUnit 4 | Development and unit testing | Eclipse Public License 1.0 | <https://github.com/junit-team/junit4> |

The application intentionally uses the non-GPL FFmpeg audio artifact. Replacing it with a GPL
variant requires a deliberate licensing and distribution review.

Before a public release, regenerate the dependency tree, compare it with this inventory, retain
all notices shipped by the selected artifacts, and have the distribution reviewed by a qualified
person. Do not treat this file as legal advice.
