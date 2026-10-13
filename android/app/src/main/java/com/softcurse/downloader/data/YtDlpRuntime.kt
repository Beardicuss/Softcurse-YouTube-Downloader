package com.softcurse.downloader.data

import android.content.Context
import android.util.Log
import com.yausername.youtubedl_android.YoutubeDL
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

/** Initializes yt-dlp once and refreshes it independently from the APK when possible. */
object YtDlpRuntime {
    private val updateLock = Mutex()

    @Volatile
    private var ready = false

    suspend fun ensureCurrent(context: Context) {
        if (ready) return
        updateLock.withLock {
            if (ready) return
            YoutubeDL.init(context.applicationContext)
            runCatching {
                YoutubeDL.updateYoutubeDL(context.applicationContext, YoutubeDL.UpdateChannel.NIGHTLY)
            }.onFailure { error ->
                Log.w(TAG, "Could not refresh yt-dlp; continuing with bundled runtime", error)
            }
            ready = true
        }
    }

    private const val TAG = "YtDlpRuntime"
}
