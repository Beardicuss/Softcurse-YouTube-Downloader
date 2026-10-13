package com.softcurse.downloader.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface DownloadDao {
    @Query("SELECT * FROM downloads WHERE state IN ('Pending', 'Running') ORDER BY createdAt ASC")
    fun observeAll(): Flow<List<DownloadEntity>>

    @Query("SELECT * FROM downloads WHERE state IN ('Complete', 'Failed', 'Cancelled') ORDER BY updatedAt DESC")
    fun observeHistory(): Flow<List<DownloadEntity>>

    @Query("SELECT * FROM downloads WHERE state IN ('Pending', 'Running') ORDER BY createdAt ASC")
    suspend fun active(): List<DownloadEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: DownloadEntity)

    @Query("UPDATE downloads SET state = :state, progress = :progress, updatedAt = :updatedAt, errorMessage = :error WHERE id = :id")
    suspend fun updateState(
        id: String,
        state: String,
        progress: Int,
        updatedAt: Long = System.currentTimeMillis(),
        error: String? = null,
    )

    @Query("UPDATE downloads SET state = 'Running', progress = :progress, errorMessage = NULL, updatedAt = :updatedAt WHERE id = :id AND state IN ('Pending', 'Running')")
    suspend fun markRunningIfActive(
        id: String,
        progress: Int = 0,
        updatedAt: Long = System.currentTimeMillis(),
    ): Int

    @Query("UPDATE downloads SET progress = :progress, updatedAt = :updatedAt WHERE id = :id AND state = 'Running'")
    suspend fun updateProgressIfRunning(
        id: String,
        progress: Int,
        updatedAt: Long = System.currentTimeMillis(),
    ): Int

    @Query("UPDATE downloads SET state = 'Complete', progress = 100, outputPath = :path, errorMessage = NULL, updatedAt = :updatedAt WHERE id = :id AND state = 'Running'")
    suspend fun completeIfRunning(
        id: String,
        path: String,
        updatedAt: Long = System.currentTimeMillis(),
    ): Int

    @Query("UPDATE downloads SET state = 'Complete', progress = 100, errorMessage = NULL, updatedAt = :updatedAt WHERE id = :id AND state = 'Running'")
    suspend fun completeSimulationIfRunning(
        id: String,
        updatedAt: Long = System.currentTimeMillis(),
    ): Int

    @Query("UPDATE downloads SET outputPath = :path, updatedAt = :updatedAt WHERE id = :id")
    suspend fun setOutputPath(id: String, path: String, updatedAt: Long = System.currentTimeMillis())

    @Query("UPDATE downloads SET state = 'Pending', progress = 0, outputPath = NULL, errorMessage = NULL, updatedAt = :updatedAt WHERE id = :id AND state IN ('Failed', 'Cancelled')")
    suspend fun prepareRetry(
        id: String,
        updatedAt: Long = System.currentTimeMillis(),
    ): Int

    @Query("SELECT * FROM downloads WHERE id = :id LIMIT 1")
    suspend fun find(id: String): DownloadEntity?

    @Query("DELETE FROM downloads WHERE id = :id")
    suspend fun delete(id: String)
}
