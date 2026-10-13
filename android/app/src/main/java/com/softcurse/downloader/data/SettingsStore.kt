package com.softcurse.downloader.data

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.softcurse.downloader.domain.MediaFormat
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.settingsDataStore by preferencesDataStore("settings_v1")

data class AppSettings(
    val defaultFormat: MediaFormat = MediaFormat.Mp3,
    val reducedMotion: Boolean = false,
    val wifiOnly: Boolean = false,
    val experimentalEngine: Boolean = false,
)

class SettingsStore(private val context: Context) {
    private object Keys {
        val defaultFormat = stringPreferencesKey("default_format")
        val reducedMotion = booleanPreferencesKey("reduced_motion")
        val wifiOnly = booleanPreferencesKey("wifi_only")
        val experimentalEngine = booleanPreferencesKey("experimental_engine")
    }

    val settings: Flow<AppSettings> = context.settingsDataStore.data.map { values ->
        AppSettings(
            defaultFormat = MediaFormat.entries.firstOrNull {
                it.name == values[Keys.defaultFormat]
            } ?: MediaFormat.Mp3,
            reducedMotion = values[Keys.reducedMotion] ?: false,
            wifiOnly = values[Keys.wifiOnly] ?: false,
            experimentalEngine = values[Keys.experimentalEngine] ?: false,
        )
    }

    suspend fun setDefaultFormat(format: MediaFormat) {
        context.settingsDataStore.edit { it[Keys.defaultFormat] = format.name }
    }

    suspend fun setReducedMotion(enabled: Boolean) {
        context.settingsDataStore.edit { it[Keys.reducedMotion] = enabled }
    }

    suspend fun setWifiOnly(enabled: Boolean) {
        context.settingsDataStore.edit { it[Keys.wifiOnly] = enabled }
    }

    suspend fun setExperimentalEngine(enabled: Boolean) {
        context.settingsDataStore.edit { it[Keys.experimentalEngine] = enabled }
    }
}
