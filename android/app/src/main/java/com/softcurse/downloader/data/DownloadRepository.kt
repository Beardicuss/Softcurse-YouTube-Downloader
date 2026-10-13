package com.softcurse.downloader.data

import android.content.Context
import androidx.work.Constraints
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkInfo
import androidx.work.workDataOf
import com.softcurse.downloader.domain.DownloadRequest
import com.softcurse.downloader.domain.DownloadState
import com.softcurse.downloader.domain.QueueItem
import com.softcurse.downloader.domain.SourcePreview
import com.softcurse.downloader.worker.FakeDownloadWorker
import com.softcurse.downloader.worker.OnDeviceDownloadWorker
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.nio.charset.StandardCharsets
import java.util.UUID

class DownloadRepository(
    private val dao: DownloadDao,
    private val workManager: WorkManager,
) {
    val downloads: Flow<List<QueueItem>> = dao.observeAll().map { rows -> rows.map { it.toDomain() } }
    val history: Flow<List<QueueItem>> = dao.observeHistory().map { rows -> rows.map { it.toDomain() } }

    suspend fun enqueue(request: DownloadRequest, wifiOnly: Boolean, experimentalEngine: Boolean) {
        dao.upsert(request.toEntity())
        schedule(request.id, wifiOnly, experimentalEngine)
    }

    suspend fun enqueuePlaylist(
        template: DownloadRequest,
        preview: SourcePreview,
        selectedMediaIds: Set<String>,
        wifiOnly: Boolean,
        experimentalEngine: Boolean,
    ): Int {
        val selected = preview.entries.filter { it.mediaId in selectedMediaIds }
        var scheduled = 0
        selected.forEach { entry ->
            val request = template.copy(
                    id = playlistEntryId(preview.playlistId ?: preview.sourceUrl, entry.mediaId, template),
                    url = entry.url,
                    title = entry.title,
                    playlistId = preview.playlistId ?: preview.sourceUrl,
                    playlistTitle = preview.title,
                    playlistIndex = entry.index,
                    playlistCount = preview.entries.size,
                )
            when (dao.find(request.id)?.state) {
                DownloadState.Complete.name,
                DownloadState.Pending.name,
                DownloadState.Running.name,
                -> Unit
                DownloadState.Failed.name,
                DownloadState.Cancelled.name,
                -> {
                    retry(request.id, wifiOnly, experimentalEngine)
                    scheduled++
                }
                else -> {
                    enqueue(request, wifiOnly, experimentalEngine)
                    scheduled++
                }
            }
        }
        return scheduled
    }

    suspend fun retry(id: String, wifiOnly: Boolean, experimentalEngine: Boolean) {
        if (dao.prepareRetry(id) == 0) return
        schedule(id, wifiOnly, experimentalEngine)
    }

    private fun schedule(id: String, wifiOnly: Boolean, experimentalEngine: Boolean) {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(if (wifiOnly) NetworkType.UNMETERED else NetworkType.CONNECTED)
            .build()
        val work = if (experimentalEngine) {
            OneTimeWorkRequestBuilder<OnDeviceDownloadWorker>()
        } else {
            OneTimeWorkRequestBuilder<FakeDownloadWorker>()
        }.setInputData(workDataOf(FakeDownloadWorker.KEY_ID to id))
            .setConstraints(constraints)
            .addTag(id)
            .build()
        workManager.enqueueUniqueWork(id, androidx.work.ExistingWorkPolicy.REPLACE, work)
    }

    suspend fun cancel(id: String) {
        dao.updateState(id, DownloadState.Cancelled.name, 0)
        workManager.cancelUniqueWork(id)
    }

    suspend fun delete(id: String) {
        workManager.cancelUniqueWork(id)
        dao.delete(id)
    }

    suspend fun reconcileActiveWork() = withContext(Dispatchers.IO) {
        dao.active().forEach { row ->
            val states = runCatching {
                workManager.getWorkInfosForUniqueWork(row.id).get().map { it.state }
            }.getOrElse { return@forEach }
            if (!hasRecoverableWork(states)) {
                dao.updateState(
                    id = row.id,
                    state = DownloadState.Failed.name,
                    progress = row.progress,
                    error = "Download was interrupted and could not be recovered",
                )
            }
        }
    }
}

internal fun hasRecoverableWork(states: List<WorkInfo.State>): Boolean = states.any {
    it == WorkInfo.State.ENQUEUED || it == WorkInfo.State.RUNNING || it == WorkInfo.State.BLOCKED
}

class AppContainer(context: Context) {
    private val database = SoftcurseDatabase.get(context)
    val settings = SettingsStore(context)
    val crashReports = CrashReportStore(context.applicationContext)
    val playlists = PlaylistResolver(context.applicationContext)
    val downloads = DownloadRepository(database.downloadDao(), WorkManager.getInstance(context))
}

internal fun playlistEntryId(playlistId: String, mediaId: String, request: DownloadRequest): String =
    UUID.nameUUIDFromBytes(
        "$playlistId|$mediaId|${request.format.name}|${request.quality}".toByteArray(StandardCharsets.UTF_8),
    ).toString()
