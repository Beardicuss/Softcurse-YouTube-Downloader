package com.softcurse.downloader.worker

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.pm.ServiceInfo
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.work.CoroutineWorker
import androidx.work.ForegroundInfo
import androidx.work.WorkerParameters
import androidx.work.workDataOf
import com.softcurse.downloader.R
import com.softcurse.downloader.data.SoftcurseDatabase
import com.softcurse.downloader.domain.DownloadState
import kotlinx.coroutines.delay
import kotlinx.coroutines.CancellationException

class FakeDownloadWorker(context: Context, parameters: WorkerParameters) :
    CoroutineWorker(context, parameters) {

    private val dao = SoftcurseDatabase.get(context).downloadDao()

    override suspend fun doWork(): Result {
        val id = inputData.getString(KEY_ID) ?: return Result.failure()
        createChannel()
        setForeground(foregroundInfo(id, 0))
        if (dao.markRunningIfActive(id) == 0) return Result.failure()

        return try {
            for (progress in 10..100 step 10) {
                if (isStopped) {
                    dao.updateState(id, DownloadState.Cancelled.name, progress)
                    return Result.failure()
                }
                delay(750)
                setProgress(workDataOf(KEY_PROGRESS to progress))
                if (dao.updateProgressIfRunning(id, progress) == 0) return Result.failure()
                setForeground(foregroundInfo(id, progress))
            }
            if (dao.completeSimulationIfRunning(id) == 0) Result.failure() else Result.success()
        } catch (cancelled: CancellationException) {
            dao.updateState(id, DownloadState.Cancelled.name, 0)
            throw cancelled
        } catch (error: Exception) {
            dao.updateState(id, DownloadState.Failed.name, 0, error = error.message)
            Result.failure()
        }
    }

    private fun createChannel() {
        val manager = applicationContext.getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(
            NotificationChannel(CHANNEL_ID, "Downloads", NotificationManager.IMPORTANCE_LOW),
        )
    }

    private fun foregroundInfo(id: String, progress: Int): ForegroundInfo {
        val notification = NotificationCompat.Builder(applicationContext, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle("Softcurse download simulation")
            .setContentText("Progress: $progress%")
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
        const val KEY_ID = "download_id"
        const val KEY_PROGRESS = "progress"
        private const val CHANNEL_ID = "downloads"
    }
}
