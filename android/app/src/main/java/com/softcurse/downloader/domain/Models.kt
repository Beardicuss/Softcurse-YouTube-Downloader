package com.softcurse.downloader.domain

import java.net.URI
import java.util.UUID

enum class MediaFormat(val label: String) {
    Mp3("MP3"),
    Flac("FLAC"),
    Wav("WAV"),
    Mp4("MP4"),
}

enum class DownloadState {
    Pending,
    Running,
    Complete,
    Failed,
    Cancelled,
}

data class DownloadRequest(
    val id: String = UUID.randomUUID().toString(),
    val url: String,
    val format: MediaFormat,
    val quality: String,
)

data class QueueItem(
    val request: DownloadRequest,
    val state: DownloadState = DownloadState.Pending,
    val progress: Int = 0,
    val outputUri: String? = null,
    val errorMessage: String? = null,
)

interface DownloadEngine {
    suspend fun enqueue(request: DownloadRequest): QueueItem
    suspend fun cancel(id: String)
}

fun validateMediaUrl(value: String): Result<String> = runCatching {
    val normalized = value.trim()
    val uri = URI(normalized)
    require(uri.scheme in setOf("http", "https")) { "Use an HTTP or HTTPS link" }
    require(!uri.host.isNullOrBlank()) { "Enter a complete media link" }
    normalized
}
