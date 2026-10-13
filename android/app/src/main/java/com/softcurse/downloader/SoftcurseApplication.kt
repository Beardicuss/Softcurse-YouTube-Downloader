package com.softcurse.downloader

import android.app.Application
import com.softcurse.downloader.data.AppContainer

class SoftcurseApplication : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
        val previousHandler = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, error ->
            runCatching { container.crashReports.capture(thread, error) }
            if (previousHandler != null) {
                previousHandler.uncaughtException(thread, error)
            } else {
                android.os.Process.killProcess(android.os.Process.myPid())
                kotlin.system.exitProcess(10)
            }
        }
    }
}
