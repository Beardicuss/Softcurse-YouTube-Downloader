package com.softcurse.downloader.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.softcurse.downloader.data.AppSettings
import com.softcurse.downloader.domain.MediaFormat
import com.softcurse.downloader.ui.components.*
import com.softcurse.downloader.ui.theme.*

@Composable
fun SettingsScreen(
    settings: AppSettings,
    onDefaultFormat: (MediaFormat) -> Unit,
    onReducedMotion: (Boolean) -> Unit,
    onWifiOnly: (Boolean) -> Unit,
    onExperimentalEngine: (Boolean) -> Unit,
    notificationsAllowed: Boolean,
    onRequestNotifications: () -> Unit,
    onOpenAbout: () -> Unit,
) {
    Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        SectionLead("Control matrix", "System configuration", "Tune transfer behavior, motion and runtime permissions.")
        SystemPanel(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Text("DEFAULT OUTPUT", color = HexCyan, style = MaterialTheme.typography.labelLarge)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    MediaFormat.entries.forEach { format ->
                        FilterChip(selected = settings.defaultFormat == format, onClick = { onDefaultFormat(format) }, label = { Text(format.label) })
                    }
                }
                SettingSwitch("NETWORK LOCK", "Only start transfers over Wi-Fi", settings.wifiOnly, onWifiOnly)
                SettingSwitch("REDUCED MOTION", "Freeze background signal animation", settings.reducedMotion, onReducedMotion)
            }
        }
        SystemPanel(Modifier.fillMaxWidth(), HexGold) {
            Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                SettingSwitch("ON-DEVICE ENGINE", "Experimental yt-dlp + FFmpeg runtime", settings.experimentalEngine, onExperimentalEngine)
                Text("Downloads real media to Download/Softcurse. Keep disabled for the simulated UI pipeline.", color = HexTextMuted)
                StatusPill(if (settings.experimentalEngine) "POC ACTIVE" else "SIMULATOR ACTIVE", if (settings.experimentalEngine) HexGold else HexCyan)
            }
        }
        SystemPanel(Modifier.fillMaxWidth(), if (notificationsAllowed) HexSignalGreen else HexCoral) {
            Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("NOTIFICATION LINK", style = MaterialTheme.typography.labelLarge)
                Text(if (notificationsAllowed) "Permission online. Background progress can be displayed." else "Permission offline. Android 13+ requires access for download status.", color = HexTextMuted)
                if (!notificationsAllowed) OutlinedButton(onClick = onRequestNotifications, modifier = Modifier.fillMaxWidth()) { Text("AUTHORIZE NOTIFICATIONS") }
            }
        }
        SystemPanel(Modifier.fillMaxWidth(), HexMagenta) {
            Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("ABOUT // PRIVACY // LICENSES", color = HexMagenta, style = MaterialTheme.typography.labelLarge)
                Text("Review local-data handling, network behavior, permissions, third-party software, and release identity.", color = HexTextMuted)
                OutlinedButton(onClick = onOpenAbout, modifier = Modifier.fillMaxWidth()) {
                    Text("OPEN ABOUT & LEGAL")
                }
            }
        }
    }
}

@Composable
private fun SettingSwitch(title: String, detail: String, checked: Boolean, onChange: (Boolean) -> Unit) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        Column(Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.labelLarge)
            Text(detail, color = HexTextMuted, style = MaterialTheme.typography.bodySmall)
        }
        Switch(checked = checked, onCheckedChange = onChange)
    }
}
