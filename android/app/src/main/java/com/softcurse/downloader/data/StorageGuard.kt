package com.softcurse.downloader.data

import android.content.Context
import android.os.Environment
import android.provider.Settings
import com.softcurse.downloader.BuildConfig
import java.io.File

class StorageExhaustedException(message: String) : Exception(message)

class StorageGuard internal constructor(
    private val workingDirectory: File,
    private val exportDirectory: File,
    private val availableBytes: (File) -> Long = { it.usableSpace },
) {
    constructor(context: Context) : this(
        workingDirectory = requireNotNull(context.getExternalFilesDir(null)) {
            "App storage is unavailable"
        },
        exportDirectory = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
        availableBytes = { location -> debugStorageOverride(context) ?: location.usableSpace },
    )

    fun requireDownloadHeadroom() = requireAvailable(
        workingDirectory,
        DOWNLOAD_HEADROOM_BYTES,
        "start this download",
    )

    fun requireConversionHeadroom(sourceBytes: Long) = requireAvailable(
        workingDirectory,
        sourceBytes.coerceAtLeast(0) + CONVERSION_RESERVE_BYTES,
        "convert this media",
    )

    fun requireExportHeadroom(sourceBytes: Long) = requireAvailable(
        exportDirectory,
        sourceBytes.coerceAtLeast(0) + EXPORT_RESERVE_BYTES,
        "save this media",
    )

    private fun requireAvailable(location: File, required: Long, phase: String) {
        val available = availableBytes(location).coerceAtLeast(0)
        if (available < required) {
            throw StorageExhaustedException(
                "Not enough storage to $phase. Free at least ${formatBytes(required - available)} and try again.",
            )
        }
    }

    companion object {
        internal const val DOWNLOAD_HEADROOM_BYTES = 512L * 1024 * 1024
        internal const val CONVERSION_RESERVE_BYTES = 128L * 1024 * 1024
        internal const val EXPORT_RESERVE_BYTES = 64L * 1024 * 1024
    }
}

private fun debugStorageOverride(context: Context): Long? {
    if (!BuildConfig.DEBUG) return null
    return runCatching {
        Settings.Global.getString(context.contentResolver, DEBUG_STORAGE_KEY)?.toLongOrNull()
    }.getOrNull()?.takeIf { it >= 0 }
}

internal const val DEBUG_STORAGE_KEY = "softcurse_debug_storage_bytes"

internal fun storageFailureMessage(error: Throwable): String? {
    var current: Throwable? = error
    while (current != null) {
        if (current is StorageExhaustedException) return current.message
        val message = current.message.orEmpty()
        if (message.contains("ENOSPC", ignoreCase = true) ||
            message.contains("no space left", ignoreCase = true) ||
            message.contains("disk full", ignoreCase = true)
        ) {
            return "Device storage is full. Free space and try the download again."
        }
        current = current.cause
    }
    return null
}

private fun formatBytes(bytes: Long): String {
    val mib = (bytes + 1024 * 1024 - 1) / (1024 * 1024)
    return if (mib >= 1024) "%.1f GiB".format(mib / 1024.0) else "$mib MiB"
}
