package com.softcurse.downloader.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.softcurse.downloader.data.AppContainer
import com.softcurse.downloader.data.AppSettings
import com.softcurse.downloader.domain.DownloadRequest
import com.softcurse.downloader.domain.MediaFormat
import com.softcurse.downloader.domain.QueueItem
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class AppViewModel(private val container: AppContainer) : ViewModel() {
    init {
        viewModelScope.launch { container.downloads.reconcileActiveWork() }
    }

    val downloads: StateFlow<List<QueueItem>> = container.downloads.downloads.stateIn(
        viewModelScope,
        SharingStarted.WhileSubscribed(5_000),
        emptyList(),
    )
    val history: StateFlow<List<QueueItem>> = container.downloads.history.stateIn(
        viewModelScope,
        SharingStarted.WhileSubscribed(5_000),
        emptyList(),
    )
    val settings: StateFlow<AppSettings> = container.settings.settings.stateIn(
        viewModelScope,
        SharingStarted.WhileSubscribed(5_000),
        AppSettings(),
    )

    fun enqueue(request: DownloadRequest) = viewModelScope.launch {
        container.downloads.enqueue(
            request,
            settings.value.wifiOnly,
            settings.value.experimentalEngine,
        )
    }

    fun cancel(id: String) = viewModelScope.launch { container.downloads.cancel(id) }
    fun delete(id: String) = viewModelScope.launch { container.downloads.delete(id) }
    fun retry(id: String) = viewModelScope.launch {
        container.downloads.retry(
            id,
            settings.value.wifiOnly,
            settings.value.experimentalEngine,
        )
    }
    fun setDefaultFormat(value: MediaFormat) = viewModelScope.launch {
        container.settings.setDefaultFormat(value)
    }
    fun setReducedMotion(value: Boolean) = viewModelScope.launch {
        container.settings.setReducedMotion(value)
    }
    fun setWifiOnly(value: Boolean) = viewModelScope.launch {
        container.settings.setWifiOnly(value)
    }
    fun setExperimentalEngine(value: Boolean) = viewModelScope.launch {
        container.settings.setExperimentalEngine(value)
    }

    companion object {
        fun factory(container: AppContainer): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T =
                    AppViewModel(container) as T
            }
    }
}
