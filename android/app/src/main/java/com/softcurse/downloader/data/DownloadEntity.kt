package com.softcurse.downloader.data

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.softcurse.downloader.domain.DownloadRequest
import com.softcurse.downloader.domain.DownloadState
import com.softcurse.downloader.domain.MediaFormat
import com.softcurse.downloader.domain.QueueItem

@Entity(tableName = "downloads")
data class DownloadEntity(
    @PrimaryKey val id: String,
    val url: String,
    val format: String,
    val quality: String,
    val state: String,
    val progress: Int,
    val createdAt: Long,
    val updatedAt: Long,
    val schemaVersion: Int = 2,
    val errorMessage: String? = null,
    val outputPath: String? = null,
    val title: String? = null,
    val playlistId: String? = null,
    val playlistTitle: String? = null,
    val playlistIndex: Int? = null,
    val playlistCount: Int? = null,
)

fun DownloadEntity.toDomain() = QueueItem(
    request = DownloadRequest(
        id = id,
        url = url,
        format = MediaFormat.entries.firstOrNull { it.name == format } ?: MediaFormat.Mp3,
        quality = quality,
        title = title,
        playlistId = playlistId,
        playlistTitle = playlistTitle,
        playlistIndex = playlistIndex,
        playlistCount = playlistCount,
    ),
    state = DownloadState.entries.firstOrNull { it.name == state } ?: DownloadState.Failed,
    progress = progress,
    outputUri = outputPath,
    errorMessage = errorMessage,
)

fun DownloadRequest.toEntity(now: Long = System.currentTimeMillis()) = DownloadEntity(
    id = id,
    url = url,
    format = format.name,
    quality = quality,
    state = DownloadState.Pending.name,
    progress = 0,
    createdAt = now,
    updatedAt = now,
    schemaVersion = 3,
    title = title,
    playlistId = playlistId,
    playlistTitle = playlistTitle,
    playlistIndex = playlistIndex,
    playlistCount = playlistCount,
)
