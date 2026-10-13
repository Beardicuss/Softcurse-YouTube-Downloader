package com.softcurse.downloader.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class UrlValidationTest {
    @Test
    fun acceptsHttpAndHttpsLinks() {
        assertEquals("https://example.com/watch?v=1", validateMediaUrl(" https://example.com/watch?v=1 ").getOrThrow())
        assertEquals("http://example.com/media", validateMediaUrl("http://example.com/media").getOrThrow())
    }

    @Test
    fun rejectsIncompleteAndUnsupportedLinks() {
        assertTrue(validateMediaUrl("youtube.com/watch?v=1").isFailure)
        assertTrue(validateMediaUrl("ftp://example.com/media").isFailure)
        assertTrue(validateMediaUrl("https://").isFailure)
    }
}
