package com.softcurse.downloader.worker

import java.util.concurrent.ExecutionException
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class NetworkFailureMessageTest {
    @Test
    fun `recognizes wrapped yt-dlp connection abort`() {
        val error = ExecutionException(
            IllegalStateException("DownloadError: [Errno 103] Software caused connection abort"),
        )

        assertEquals(
            "Network connection lost. Restore your connection, then retry the transfer.",
            networkFailureMessage(error, networkConnected = true),
        )
    }

    @Test
    fun `uses connectivity state when exception has no network wording`() {
        assertEquals(
            "Network connection lost. Restore your connection, then retry the transfer.",
            networkFailureMessage(IllegalStateException("Download failed"), networkConnected = false),
        )
    }

    @Test
    fun `does not relabel unrelated failure while connected`() {
        assertNull(networkFailureMessage(IllegalStateException("Unsupported format"), networkConnected = true))
    }
}
