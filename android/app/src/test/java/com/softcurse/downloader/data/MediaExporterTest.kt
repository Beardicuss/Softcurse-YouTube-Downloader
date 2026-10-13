package com.softcurse.downloader.data

import org.junit.Assert.assertEquals
import org.junit.Test

class MediaExporterTest {
    @Test
    fun mapsSupportedFormatsToMediaStoreMimeTypes() {
        assertEquals("audio/mpeg", mimeTypeFor("MP3"))
        assertEquals("audio/flac", mimeTypeFor("flac"))
        assertEquals("audio/wav", mimeTypeFor("wav"))
        assertEquals("video/mp4", mimeTypeFor("mp4"))
        assertEquals("application/octet-stream", mimeTypeFor("bin"))
    }
}
