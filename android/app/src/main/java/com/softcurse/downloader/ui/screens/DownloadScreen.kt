package com.softcurse.downloader.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AddLink
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.softcurse.downloader.domain.*
import com.softcurse.downloader.ui.components.*
import com.softcurse.downloader.ui.SourceInspectionState

@Composable
fun DownloadScreen(
    defaultFormat: MediaFormat,
    inspection: SourceInspectionState,
    onInspect: (DownloadRequest) -> Unit,
    onConfirmPlaylist: (Set<String>) -> Unit,
    onDismissInspection: () -> Unit,
) {
    var url by remember { mutableStateOf("") }
    var format by remember(defaultFormat) { mutableStateOf(defaultFormat) }
    var error by remember { mutableStateOf<String?>(null) }
    val playlistState = inspection as? SourceInspectionState.PlaylistReady
    var selectedEntries by remember(playlistState?.preview) {
        mutableStateOf(playlistState?.preview?.entries?.map { it.mediaId }?.toSet().orEmpty())
    }

    if (playlistState != null) {
        AlertDialog(
            onDismissRequest = onDismissInspection,
            title = { Text(playlistState.preview.title) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text(
                        "${playlistState.preview.entries.size} entries detected" +
                            if (playlistState.preview.truncated) " // first 100 shown" else "",
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        TextButton(onClick = { selectedEntries = playlistState.preview.entries.map { it.mediaId }.toSet() }) { Text("SELECT ALL") }
                        TextButton(onClick = { selectedEntries = emptySet() }) { Text("CLEAR") }
                    }
                    LazyColumn(modifier = Modifier.heightIn(max = 360.dp)) {
                        items(playlistState.preview.entries, key = { it.mediaId }) { entry ->
                            Row(Modifier.fillMaxWidth(), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                                Checkbox(
                                    checked = entry.mediaId in selectedEntries,
                                    onCheckedChange = { checked ->
                                        selectedEntries = if (checked) selectedEntries + entry.mediaId else selectedEntries - entry.mediaId
                                    },
                                )
                                Text("${entry.index}. ${entry.title}", modifier = Modifier.weight(1f), maxLines = 2)
                            }
                        }
                    }
                }
            },
            confirmButton = {
                Button(
                    enabled = selectedEntries.isNotEmpty(),
                    onClick = { onConfirmPlaylist(selectedEntries) },
                ) { Text("QUEUE ${selectedEntries.size}") }
            },
            dismissButton = { TextButton(onClick = onDismissInspection) { Text("CANCEL") } },
        )
    }

    SystemPanel(Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(18.dp).verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(18.dp),
        ) {
            SectionLead("Input node 01", "Route media into the system", "Paste a public media link, select the output codec, then initialize the queue.")
            MetricRow {
                Metric("Pipeline", "READY")
                Metric("Output", format.label)
                Metric("Mode", "MANUAL")
            }
            OutlinedTextField(
                value = url,
                onValueChange = { url = it; error = null },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("MEDIA SOURCE URL") },
                placeholder = { Text("https://…") },
                leadingIcon = { Icon(Icons.Outlined.AddLink, contentDescription = null) },
                singleLine = true,
                isError = error != null,
                supportingText = error?.let { message -> { Text(message) } },
            )
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("OUTPUT PROTOCOL", style = MaterialTheme.typography.labelLarge)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    MediaFormat.entries.forEach { option ->
                        FilterChip(selected = format == option, onClick = { format = option }, label = { Text(option.label) })
                    }
                }
            }
            Button(
                modifier = Modifier.fillMaxWidth(),
                enabled = inspection !is SourceInspectionState.Inspecting,
                onClick = {
                    validateMediaUrl(url).fold(
                        onSuccess = { validUrl ->
                            onInspect(DownloadRequest(url = validUrl, format = format, quality = if (format == MediaFormat.Mp4) "1080p" else "320 kbps"))
                        },
                        onFailure = { error = it.message ?: "Invalid link" },
                    )
                },
            ) {
                Text(if (inspection is SourceInspectionState.Inspecting) "INSPECTING SOURCE…" else "INITIALIZE DOWNLOAD")
            }
            when (inspection) {
                is SourceInspectionState.Failed -> Text(inspection.message, color = MaterialTheme.colorScheme.error)
                is SourceInspectionState.Enqueued -> Text("${inspection.count} transfer${if (inspection.count == 1) "" else "s"} queued")
                else -> Unit
            }
        }
    }
}
