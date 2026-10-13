package com.softcurse.downloader.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.softcurse.downloader.domain.DownloadState
import com.softcurse.downloader.domain.QueueItem
import com.softcurse.downloader.ui.components.*
import com.softcurse.downloader.ui.theme.*

@Composable
fun HistoryScreen(items: List<QueueItem>, onRetry: (String) -> Unit) {
    if (items.isEmpty()) {
        EmptyStateScreen("ARCHIVE EMPTY", "Completed, failed and cancelled transfers will be indexed here.")
        return
    }
    LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item {
            val complete = items.count { it.state == DownloadState.Complete }
            SectionLead("Archive core", "Transfer records", "$complete completed // ${items.size - complete} interrupted")
        }
        items(items, key = { it.request.id }) { item ->
            val color = if (item.state == DownloadState.Complete) HexSignalGreen else HexCoral
            SystemPanel(Modifier.fillMaxWidth(), color) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        StatusPill(item.state.name, color)
                        Text("${item.request.format.label} // ${item.request.quality}", color = HexCyan, style = MaterialTheme.typography.labelLarge)
                    }
                    item.request.playlistTitle?.let { playlist ->
                        Text(
                            "$playlist // ${item.request.playlistIndex}/${item.request.playlistCount}",
                            color = HexTextMuted,
                            style = MaterialTheme.typography.labelMedium,
                        )
                    }
                    Text(item.request.title ?: item.request.url, maxLines = 2, overflow = TextOverflow.Ellipsis)
                    item.errorMessage?.let { Text(it, color = HexCoral, style = MaterialTheme.typography.bodyMedium) }
                    Text("NODE ${item.request.id.take(8).uppercase()}", color = HexTextMuted, style = MaterialTheme.typography.labelSmall)
                    if (item.state == DownloadState.Failed) {
                        OutlinedButton(
                            modifier = Modifier.fillMaxWidth(),
                            onClick = { onRetry(item.request.id) },
                        ) { Text("RETRY TRANSFER") }
                    }
                }
            }
        }
    }
}
