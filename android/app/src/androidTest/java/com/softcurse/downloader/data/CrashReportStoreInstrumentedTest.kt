package com.softcurse.downloader.data

import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class CrashReportStoreInstrumentedTest {
    @Test
    fun reportIsStoredPrivatelyAndCanBeDeleted() {
        val store = CrashReportStore(ApplicationProvider.getApplicationContext())
        store.clear()

        store.capture(Thread.currentThread(), IllegalStateException("physical diagnostics test"))

        assertTrue(store.latestReport.value.orEmpty().contains("physical diagnostics test"))
        store.clear()
        assertNull(store.latestReport.value)
    }
}
