package com.softcurse.downloader.ui.screens

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class OpenSourceComponentsTest {
    @Test
    fun `release runtime components have license and secure source links`() {
        val required = listOf("AndroidX", "Kotlin", "yt-dlp", "CPython", "FFmpeg")

        required.forEach { name ->
            assertTrue(openSourceComponents.any { component -> component.name.contains(name, ignoreCase = true) })
        }
        assertTrue(openSourceComponents.all { it.license.isNotBlank() })
        assertTrue(openSourceComponents.all { it.sourceUrl.startsWith("https://") })
        assertEquals(openSourceComponents.size, openSourceComponents.map { it.name }.distinct().size)
    }
}
