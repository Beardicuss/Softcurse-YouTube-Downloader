package com.softcurse.downloader.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.softcurse.downloader.domain.*
import com.softcurse.downloader.ui.components.*
import com.softcurse.downloader.ui.theme.*

@Composable
fun QueueScreen(items: List<QueueItem>, onCancel: (String) -> Unit, onRemove: (String) -> Unit) {
    if (items.isEmpty()) {
        EmptyStateScreen("QUEUE OFFLINE", "Add a media link from Download to activate the transfer network.")
        return
    }
    LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item { SectionLead("Transfer matrix", "${items.size} active node${if (items.size == 1) "" else "s"}", "Live job telemetry and queue controls.") }
        items(items, key = { it.request.id }) { item ->
            val active = item.state == DownloadState.Pending || item.state == DownloadState.Running
            val accent = stateColor(item.state)
            SystemPanel(modifier = Modifier.fillMaxWidth(), accent = accent, darkGlass = true) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        StatusPill(item.state.name, accent)
                        Text(item.request.format.label, color = HexCyan, style = MaterialTheme.typography.labelLarge)
                    }
                    Text(item.request.url, maxLines = 2, overflow = TextOverflow.Ellipsis)
                    item.errorMessage?.let { Text(it, color = HexGold, style = MaterialTheme.typography.bodyMedium) }
                    LinearProgressIndicator(progress = { item.progress / 100f }, modifier = Modifier.fillMaxWidth(), color = accent, trackColor = accent.copy(alpha = 0.12f))
                    MetricRow {
                        Metric("Progress", "${item.progress}%", accent)
                        Metric("Quality", item.request.quality)
                    }
                    OutlinedButton(modifier = Modifier.fillMaxWidth(), onClick = { if (active) onCancel(item.request.id) else onRemove(item.request.id) }) {
                        Text(if (active) "ABORT TRANSFER" else "CLEAR NODE")
                    }
                }
            }
        }
    }
}

@Composable
fun EmptyStateScreen(title: String, detail: String) {
    SystemPanel(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("SYSTEM // STANDBY", color = HexTextMuted, style = MaterialTheme.typography.labelLarge)
            Text(title, color = HexCyan, style = MaterialTheme.typography.titleLarge)
            Text(detail, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

private fun stateColor(state: DownloadState): Color = when (state) {
    DownloadState.Running, DownloadState.Complete -> HexSignalGreen
    DownloadState.Pending -> HexGold
    DownloadState.Failed, DownloadState.Cancelled -> HexCoral
}
