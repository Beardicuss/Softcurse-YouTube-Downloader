package com.softcurse.downloader.data

import com.softcurse.downloader.domain.DownloadEngine
import com.softcurse.downloader.domain.DownloadRequest
import com.softcurse.downloader.domain.QueueItem

class FakeDownloadEngine : DownloadEngine {
    override suspend fun enqueue(request: DownloadRequest): QueueItem = QueueItem(request)

    override suspend fun cancel(id: String) = Unit
}
