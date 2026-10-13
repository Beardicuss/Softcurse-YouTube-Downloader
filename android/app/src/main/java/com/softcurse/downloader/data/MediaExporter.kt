package com.softcurse.downloader.data

import android.content.ContentValues
import android.content.Context
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import java.io.File

class MediaExporter(private val context: Context) {
    fun export(source: File): String {
        StorageGuard(context).requireExportHeadroom(source.length())
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) {
            return source.absolutePath
        }

        val values = ContentValues().apply {
            put(MediaStore.MediaColumns.DISPLAY_NAME, source.name)
            put(MediaStore.MediaColumns.MIME_TYPE, mimeTypeFor(source.extension))
            put(
                MediaStore.MediaColumns.RELATIVE_PATH,
                "${Environment.DIRECTORY_DOWNLOADS}/Softcurse",
            )
            put(MediaStore.MediaColumns.IS_PENDING, 1)
        }
        val collection = MediaStore.Downloads.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY)
        val resolver = context.contentResolver
        val uri = resolver.insert(collection, values)
            ?: error("Android could not create a Downloads destination")
        try {
            resolver.openOutputStream(uri, "w")?.use { output ->
                source.inputStream().use { input -> input.copyTo(output) }
            } ?: error("Android could not open the Downloads destination")
            resolver.update(
                uri,
                ContentValues().apply { put(MediaStore.MediaColumns.IS_PENDING, 0) },
                null,
                null,
            )
            source.delete()
            return uri.toString()
        } catch (error: Exception) {
            resolver.delete(uri, null, null)
            throw error
        }
    }

    fun delete(location: String) {
        val uri = android.net.Uri.parse(location)
        if (uri.scheme == "content") {
            context.contentResolver.delete(uri, null, null)
        } else {
            File(location).delete()
        }
    }
}

internal fun mimeTypeFor(extension: String): String = when (extension.lowercase()) {
    "mp3" -> "audio/mpeg"
    "flac" -> "audio/flac"
    "wav" -> "audio/wav"
    "mp4" -> "video/mp4"
    else -> "application/octet-stream"
}
