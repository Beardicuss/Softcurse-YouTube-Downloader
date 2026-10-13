package com.softcurse.downloader.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

@Database(
    entities = [DownloadEntity::class],
    version = 3,
    exportSchema = true,
)
abstract class SoftcurseDatabase : RoomDatabase() {
    abstract fun downloadDao(): DownloadDao

    companion object {
        @Volatile private var instance: SoftcurseDatabase? = null

        fun get(context: Context): SoftcurseDatabase = instance ?: synchronized(this) {
            instance ?: Room.databaseBuilder(
                context.applicationContext,
                SoftcurseDatabase::class.java,
                "softcurse.db",
            ).addMigrations(MIGRATION_1_2, MIGRATION_2_3).build().also { instance = it }
        }

        private val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE downloads ADD COLUMN outputPath TEXT")
            }
        }

        private val MIGRATION_2_3 = object : Migration(2, 3) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE downloads ADD COLUMN title TEXT")
                db.execSQL("ALTER TABLE downloads ADD COLUMN playlistId TEXT")
                db.execSQL("ALTER TABLE downloads ADD COLUMN playlistTitle TEXT")
                db.execSQL("ALTER TABLE downloads ADD COLUMN playlistIndex INTEGER")
                db.execSQL("ALTER TABLE downloads ADD COLUMN playlistCount INTEGER")
                db.execSQL("UPDATE downloads SET schemaVersion = 3")
            }
        }
    }
}
