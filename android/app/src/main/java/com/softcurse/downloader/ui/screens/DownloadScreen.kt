package com.softcurse.downloader.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AddLink
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.softcurse.downloader.domain.*
import com.softcurse.downloader.ui.components.*

@Composable
fun DownloadScreen(defaultFormat: MediaFormat, onEnqueue: (QueueItem) -> Unit) {
    var url by remember { mutableStateOf("") }
    var format by remember(defaultFormat) { mutableStateOf(defaultFormat) }
    var error by remember { mutableStateOf<String?>(null) }

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
                onClick = {
                    validateMediaUrl(url).fold(
                        onSuccess = { validUrl ->
                            onEnqueue(QueueItem(DownloadRequest(url = validUrl, format = format, quality = if (format == MediaFormat.Mp4) "1080p" else "320 kbps")))
                            url = ""
                        },
                        onFailure = { error = it.message ?: "Invalid link" },
                    )
                },
            ) { Text("INITIALIZE DOWNLOAD") }
        }
    }
}
