package com.softcurse.downloader.data

import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class StorageGuardTest {
    private val location = File(".")

    @Test
    fun downloadGateRejectsInsufficientSpaceWithActionableMessage() {
        val guard = StorageGuard(location, location) { 0L }

        val error = runCatching { guard.requireDownloadHeadroom() }.exceptionOrNull()

        assertTrue(error is StorageExhaustedException)
        assertTrue(error?.message.orEmpty().contains("Free at least 512 MiB"))
    }

    @Test
    fun conversionAndExportIncludeSourcePlusReserve() {
        val source = 100L * 1024 * 1024
        val conversion = StorageGuard(location, location) { source + StorageGuard.CONVERSION_RESERVE_BYTES - 1 }
        val export = StorageGuard(location, location) { source + StorageGuard.EXPORT_RESERVE_BYTES - 1 }

        assertTrue(runCatching { conversion.requireConversionHeadroom(source) }.exceptionOrNull() is StorageExhaustedException)
        assertTrue(runCatching { export.requireExportHeadroom(source) }.exceptionOrNull() is StorageExhaustedException)
    }

    @Test
    fun exactCapacityPassesAndNestedEnospcIsNormalized() {
        StorageGuard(location, location) { StorageGuard.DOWNLOAD_HEADROOM_BYTES }.requireDownloadHeadroom()
        val wrapped = IllegalStateException("wrapper", java.io.IOException("ENOSPC: No space left on device"))

        assertEquals(
            "Device storage is full. Free space and try the download again.",
            storageFailureMessage(wrapped),
        )
    }
}
