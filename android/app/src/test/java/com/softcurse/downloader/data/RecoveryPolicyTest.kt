package com.softcurse.downloader.data

import androidx.work.WorkInfo
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class RecoveryPolicyTest {
    @Test
    fun runnableWorkKeepsPersistedJobActive() {
        assertTrue(hasRecoverableWork(listOf(WorkInfo.State.ENQUEUED)))
        assertTrue(hasRecoverableWork(listOf(WorkInfo.State.RUNNING)))
        assertTrue(hasRecoverableWork(listOf(WorkInfo.State.BLOCKED)))
    }

    @Test
    fun terminalOrMissingWorkCannotRecoverPersistedJob() {
        assertFalse(hasRecoverableWork(emptyList()))
        assertFalse(hasRecoverableWork(listOf(WorkInfo.State.SUCCEEDED)))
        assertFalse(hasRecoverableWork(listOf(WorkInfo.State.FAILED, WorkInfo.State.CANCELLED)))
    }
}
