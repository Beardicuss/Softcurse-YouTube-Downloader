package com.softcurse.downloader.data

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CrashReportStoreTest {
    @Test
    fun `crash report contains diagnostics and stack trace without media input`() {
        val report = buildCrashReport(
            occurredAt = "2026-10-13T12:00:00Z",
            threadName = "main",
            error = IllegalStateException("test failure"),
            appVersion = "0.1.0 (1)",
            androidVersion = "Android 13 / API 33",
            device = "Example Phone",
        )

        assertTrue(report.contains("Generated locally; review before sending."))
        assertTrue(report.contains("IllegalStateException: test failure"))
        assertTrue(report.contains("Example Phone"))
        assertFalse(report.contains("youtube.com"))
    }
}
