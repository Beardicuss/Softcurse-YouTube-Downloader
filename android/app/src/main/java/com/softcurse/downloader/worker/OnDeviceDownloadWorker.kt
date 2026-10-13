package com.softcurse.downloader.worker

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.pm.ServiceInfo
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.Build
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.work.CoroutineWorker
import androidx.work.ForegroundInfo
import androidx.work.WorkerParameters
import androidx.work.workDataOf
import com.arthenica.ffmpegkit.FFmpegKit
import com.arthenica.ffmpegkit.ReturnCode
import com.softcurse.downloader.R
import com.softcurse.downloader.data.SoftcurseDatabase
import com.softcurse.downloader.data.MediaExporter
import com.softcurse.downloader.data.StorageGuard
import com.softcurse.downloader.data.YtDlpRuntime
import com.softcurse.downloader.data.storageFailureMessage
import com.softcurse.downloader.domain.DownloadState
import com.softcurse.downloader.domain.MediaFormat
import com.yausername.youtubedl_android.YoutubeDL
import com.yausername.youtubedl_android.YoutubeDLRequest
import java.io.File
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.runInterruptible
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlin.coroutines.resume

class OnDeviceDownloadWorker(context: Context, parameters: WorkerParameters) :
    CoroutineWorker(context, parameters) {

    private val dao = SoftcurseDatabase.get(context).downloadDao()

    override suspend fun doWork(): Result {
        val id = inputData.getString(FakeDownloadWorker.KEY_ID) ?: return Result.failure()
        val row = dao.find(id) ?: return Result.failure()
        createChannel()
        setForeground(foregroundInfo(id, 0, "Preparing on-device engine"))
        if (dao.markRunningIfActive(id) == 0) return Result.failure()
        cleanupPartialFiles(id)

        return try {
            val output = withContext(Dispatchers.IO) {
                download(row.id, row.url, row.format, row.quality)
            }
            currentCoroutineContext().ensureActive()
            val exporter = MediaExporter(applicationContext)
            val exportedLocation = exporter.export(output)
            try {
                currentCoroutineContext().ensureActive()
            } catch (cancelled: CancellationException) {
                exporter.delete(exportedLocation)
                throw cancelled
            }
            if (dao.completeIfRunning(id, exportedLocation) == 0) {
                exporter.delete(exportedLocation)
                throw CancellationException("Download was cancelled before export completed")
            }
            Result.success(workDataOf(KEY_OUTPUT_PATH to exportedLocation))
        } catch (cancelled: CancellationException) {
            cleanupPartialFiles(id)
            if (dao.find(id)?.state != DownloadState.Cancelled.name) {
                val detail = if (isNetworkConnected()) {
                    "Transfer paused by Android. Waiting to retry automatically."
                } else {
                    "Network connection lost. Waiting to retry automatically."
                }
                dao.updateState(id, DownloadState.Pending.name, 0, error = detail)
            }
            throw cancelled
        } catch (error: Exception) {
            if (dao.find(id)?.state == DownloadState.Cancelled.name) {
                cleanupPartialFiles(id)
                throw CancellationException("Download cancelled").apply { initCause(error) }
            }
            Log.e(TAG, "On-device download failed for $id", error)
            cleanupPartialFiles(id)
            val detail = storageFailureMessage(error)
                ?: networkFailureMessage(error, isNetworkConnected())
                ?: error.message
                ?: "On-device download failed"
            dao.updateState(id, DownloadState.Failed.name, 0, error = detail)
            Result.failure(workDataOf(KEY_ERROR to detail))
        }
    }

    private suspend fun download(id: String, url: String, formatName: String, quality: String): File {
        val directory = downloadDirectory()
        val storage = StorageGuard(applicationContext)
        storage.requireDownloadHeadroom()
        YtDlpRuntime.ensureCurrent(applicationContext)
        val format = MediaFormat.entries.firstOrNull { it.name == formatName } ?: MediaFormat.Mp3
        val request = YoutubeDLRequest(url)
            .addOption("-o", File(directory, "$id.%(ext)s").absolutePath)
            .addOption("--no-playlist")
        if (format == MediaFormat.Mp4) {
            val height = quality.filter(Char::isDigit).ifBlank { "1080" }
            request.addOption("-f", "best[ext=mp4][height<=$height]/best[ext=mp4]/best")
        } else {
            request.addOption("-f", "bestaudio/best")
        }
        val response = try {
            runInterruptible {
                YoutubeDL.execute(request, id) { progress, _, line ->
                    val value = progress.toInt().coerceIn(0, 95)
                    setProgressAsync(workDataOf(FakeDownloadWorker.KEY_PROGRESS to value))
                    setForegroundAsync(foregroundInfo(id, value, line.take(80)))
                    val stillRunning = runBlocking { dao.updateProgressIfRunning(id, value) > 0 }
                    if (isStopped || !stillRunning) {
                        YoutubeDL.destroyProcessById(id)
                        throw CancellationException("Download cancelled")
                    }
                }
            }
        } catch (cancelled: CancellationException) {
            YoutubeDL.destroyProcessById(id)
            throw cancelled
        }
        check(response.exitCode == 0) { "yt-dlp exited with code ${response.exitCode}" }
        currentCoroutineContext().ensureActive()

        val downloaded = directory.listFiles()?.firstOrNull { it.name.startsWith("$id.") }
            ?: error("Downloaded file was not produced")
        if (format == MediaFormat.Mp4) return downloaded

        storage.requireConversionHeadroom(downloaded.length())
        val converted = File(directory, "$id.${format.label.lowercase()}")
        val session = executeFfmpegCancellable("-y -i ${quote(downloaded.absolutePath)} ${quote(converted.absolutePath)}")
        check(ReturnCode.isSuccess(session.returnCode)) {
            "FFmpeg conversion failed: ${session.failStackTrace ?: session.output}"
        }
        if (downloaded != converted) downloaded.delete()
        return converted
    }

    private suspend fun executeFfmpegCancellable(command: String) = suspendCancellableCoroutine { continuation ->
        val session = FFmpegKit.executeAsync(command) { completed ->
            if (continuation.isActive) continuation.resume(completed)
        }
        continuation.invokeOnCancellation { FFmpegKit.cancel(session.sessionId) }
    }

    private fun downloadDirectory() =
        File(applicationContext.getExternalFilesDir(null), "Downloads").apply { mkdirs() }

    private fun cleanupPartialFiles(id: String) {
        downloadDirectory().listFiles()
            ?.filter { it.name == id || it.name.startsWith("$id.") }
            ?.forEach(File::delete)
    }

    private fun isNetworkConnected(): Boolean {
        val manager = applicationContext.getSystemService(ConnectivityManager::class.java)
        val network = manager.activeNetwork ?: return false
        val capabilities = manager.getNetworkCapabilities(network) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
            capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
    }

    private fun quote(value: String) = "\"${value.replace("\"", "\\\"")}\""

    private fun createChannel() {
        applicationContext.getSystemService(NotificationManager::class.java).createNotificationChannel(
            NotificationChannel(CHANNEL_ID, "Experimental downloads", NotificationManager.IMPORTANCE_LOW),
        )
    }

    private fun foregroundInfo(id: String, progress: Int, detail: String): ForegroundInfo {
        val notification = NotificationCompat.Builder(applicationContext, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle("Softcurse on-device download")
            .setContentText(detail)
            .setOnlyAlertOnce(true)
            .setOngoing(progress < 100)
            .setProgress(100, progress, false)
            .build()
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            ForegroundInfo(
                id.hashCode().and(Int.MAX_VALUE),
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC,
            )
        } else {
            ForegroundInfo(id.hashCode().and(Int.MAX_VALUE), notification)
        }
    }

    companion object {
        const val KEY_OUTPUT_PATH = "output_path"
        const val KEY_ERROR = "error"
        private const val TAG = "OnDeviceDownloadWorker"
        private const val CHANNEL_ID = "experimental_downloads"
    }
}

internal fun networkFailureMessage(error: Throwable, networkConnected: Boolean): String? {
    val networkMarkers = listOf(
        "connection abort",
        "connection reset",
        "network is unreachable",
        "no route to host",
        "temporary failure in name resolution",
        "name or service not known",
        "timed out",
        "timeout",
    )
    var current: Throwable? = error
    while (current != null) {
        if (networkMarkers.any { marker -> current.message.orEmpty().contains(marker, ignoreCase = true) }) {
            return "Network connection lost. Restore your connection, then retry the transfer."
        }
        current = current.cause
    }
    return if (!networkConnected) {
        "Network connection lost. Restore your connection, then retry the transfer."
    } else {
        null
    }
}
