package com.softcurse.downloader

import android.app.Application
import com.softcurse.downloader.data.AppContainer

class SoftcurseApplication : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
    }
}
