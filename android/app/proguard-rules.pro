# Apache Commons Compress registers ZIP extra-field implementations by class and
# reflectively instantiates them while installing yt-dlp updates. R8 must not merge
# or abstract those implementations in release builds.
-keep class org.apache.commons.compress.archivers.zip.** { *; }
