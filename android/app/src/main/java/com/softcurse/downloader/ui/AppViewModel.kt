package com.softcurse.downloader.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.softcurse.downloader.data.AppContainer
import com.softcurse.downloader.data.AppSettings
import com.softcurse.downloader.domain.DownloadRequest
import com.softcurse.downloader.domain.MediaFormat
import com.softcurse.downloader.domain.QueueItem
import com.softcurse.downloader.domain.SourcePreview
import kotlinx.coroutines.flow.MutableStateFlow
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
    val crashReport: StateFlow<String?> = container.crashReports.latestReport

    private val _sourceInspection = MutableStateFlow<SourceInspectionState>(SourceInspectionState.Idle)
    val sourceInspection: StateFlow<SourceInspectionState> = _sourceInspection

    fun enqueue(request: DownloadRequest) = viewModelScope.launch {
        container.downloads.enqueue(
            request,
            settings.value.wifiOnly,
            settings.value.experimentalEngine,
        )
    }

    fun inspectAndEnqueue(request: DownloadRequest) = viewModelScope.launch {
        _sourceInspection.value = SourceInspectionState.Inspecting
        runCatching { container.playlists.inspect(request.url) }
            .onSuccess { preview ->
                if (preview.isPlaylist) {
                    _sourceInspection.value = SourceInspectionState.PlaylistReady(request, preview)
                } else {
                    val entry = preview.entries.single()
                    container.downloads.enqueue(
                        request.copy(url = entry.url, title = entry.title),
                        settings.value.wifiOnly,
                        settings.value.experimentalEngine,
                    )
                    _sourceInspection.value = SourceInspectionState.Enqueued(1)
                }
            }
            .onFailure { error ->
                _sourceInspection.value = SourceInspectionState.Failed(
                    error.message ?: "Could not inspect this media link",
                )
            }
    }

    fun enqueuePlaylist(selectedMediaIds: Set<String>) = viewModelScope.launch {
        val state = _sourceInspection.value as? SourceInspectionState.PlaylistReady ?: return@launch
        if (selectedMediaIds.isEmpty()) {
            _sourceInspection.value = SourceInspectionState.Failed("Select at least one playlist entry")
            return@launch
        }
        val count = container.downloads.enqueuePlaylist(
            state.request,
            state.preview,
            selectedMediaIds,
            settings.value.wifiOnly,
            settings.value.experimentalEngine,
        )
        _sourceInspection.value = SourceInspectionState.Enqueued(count)
    }

    fun clearSourceInspection() {
        _sourceInspection.value = SourceInspectionState.Idle
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

    fun clearCrashReport() = container.crashReports.clear()

    companion object {
        fun factory(container: AppContainer): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T =
                    AppViewModel(container) as T
            }
    }
}

sealed interface SourceInspectionState {
    data object Idle : SourceInspectionState
    data object Inspecting : SourceInspectionState
    data class PlaylistReady(val request: DownloadRequest, val preview: SourcePreview) : SourceInspectionState
    data class Enqueued(val count: Int) : SourceInspectionState
    data class Failed(val message: String) : SourceInspectionState
}
