package com.softcurse.downloader.ui

import com.softcurse.downloader.domain.DownloadRequest
import com.softcurse.downloader.domain.DownloadState
import com.softcurse.downloader.domain.MediaFormat
import com.softcurse.downloader.domain.QueueItem
import com.softcurse.downloader.ui.screens.playableItems
import org.junit.Assert.assertEquals
import org.junit.Test

class PlayerSelectionTest {
    @Test
    fun onlyCompletedDownloadsWithOutputArePlayable() {
        val complete = item("complete", DownloadState.Complete, "content://media/file/1")
        val simulation = item("simulation", DownloadState.Complete, null)
        val running = item("running", DownloadState.Running, "content://media/file/2")

        assertEquals(listOf(complete), playableItems(listOf(simulation, running, complete)))
    }

    private fun item(id: String, state: DownloadState, outputUri: String?) = QueueItem(
        request = DownloadRequest(id, "https://example.com/$id", MediaFormat.Mp3, "320 kbps"),
        state = state,
        progress = if (state == DownloadState.Complete) 100 else 50,
        outputUri = outputUri,
    )
}
