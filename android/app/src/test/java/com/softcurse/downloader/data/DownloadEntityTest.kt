package com.softcurse.downloader.data

import com.softcurse.downloader.domain.DownloadRequest
import com.softcurse.downloader.domain.DownloadState
import com.softcurse.downloader.domain.MediaFormat
import org.junit.Assert.assertEquals
import org.junit.Test

class DownloadEntityTest {
    @Test
    fun requestRoundTripsThroughVersionedPersistenceModel() {
        val request = DownloadRequest(
            id = "stable-id",
            url = "https://example.com/media",
            format = MediaFormat.Flac,
            quality = "lossless",
        )

        val entity = request.toEntity(now = 123L)
        val restored = entity.toDomain()

        assertEquals(3, entity.schemaVersion)
        assertEquals(request, restored.request)
        assertEquals(DownloadState.Pending, restored.state)
        assertEquals(0, restored.progress)
        assertEquals(null, restored.outputUri)
    }
}
