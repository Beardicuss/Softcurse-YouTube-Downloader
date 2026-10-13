package com.softcurse.downloader.ui.screens

import android.net.Uri
import android.widget.VideoView
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.softcurse.downloader.domain.DownloadState
import com.softcurse.downloader.domain.QueueItem
import com.softcurse.downloader.ui.components.*
import com.softcurse.downloader.ui.theme.*
import kotlinx.coroutines.delay

@Composable
fun PlayerScreen(history: List<QueueItem>) {
    val playable = remember(history) { playableItems(history) }
    if (playable.isEmpty()) {
        EmptyStateScreen("PLAYER OFFLINE", "Complete a real on-device download to make it available here. Simulated jobs do not create media files.")
        return
    }

    val context = LocalContext.current
    val videoView = remember { VideoView(context) }
    var selectedIndex by remember(playable) { mutableIntStateOf(0) }
    var prepared by remember { mutableStateOf(false) }
    var playing by remember { mutableStateOf(false) }
    var duration by remember { mutableIntStateOf(0) }
    var position by remember { mutableIntStateOf(0) }
    var error by remember { mutableStateOf<String?>(null) }
    val selected = playable[selectedIndex]

    fun prepare(index: Int) {
        selectedIndex = index.coerceIn(playable.indices)
        prepared = false
        playing = false
        duration = 0
        position = 0
        error = null
        videoView.setVideoURI(Uri.parse(playable[selectedIndex].outputUri))
        videoView.requestFocus()
    }

    DisposableEffect(videoView) {
        videoView.setOnPreparedListener { player ->
            prepared = true
            duration = player.duration.coerceAtLeast(0)
            position = 0
            player.setOnCompletionListener {
                playing = false
                position = duration
            }
        }
        videoView.setOnErrorListener { _, what, extra ->
            prepared = false
            playing = false
            error = "Playback error $what/$extra"
            true
        }
        onDispose { videoView.stopPlayback() }
    }

    LaunchedEffect(playable) {
        prepare(selectedIndex.coerceIn(playable.indices))
    }

    LaunchedEffect(playing, selected.request.id) {
        while (playing) {
            position = runCatching { videoView.currentPosition }.getOrDefault(position)
            delay(250)
        }
    }

    LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            SystemPanel(Modifier.fillMaxWidth(), HexMagenta) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                    SectionLead("Playback terminal", selected.request.format.label + " channel", selected.request.url)
                    AndroidView(
                        factory = { videoView },
                        modifier = Modifier.fillMaxWidth().height(if (selected.request.format.name == "Mp4") 190.dp else 72.dp).background(Color.Black, CutCornerShape(8.dp)),
                    )
                    MetricRow {
                        Metric("State", when { error != null -> "ERROR"; playing -> "PLAYING"; prepared -> "READY"; else -> "LOADING" }, if (error != null) HexCoral else HexMagenta)
                        Metric("Autoplay", "OFF", HexSignalGreen)
                        Metric("Track", "${selectedIndex + 1}/${playable.size}")
                    }
                    Slider(
                        value = position.toFloat(),
                        onValueChange = { value -> position = value.toInt() },
                        onValueChangeFinished = { if (prepared) videoView.seekTo(position) },
                        valueRange = 0f..duration.coerceAtLeast(1).toFloat(),
                        enabled = prepared,
                    )
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(formatTime(position), color = HexTextMuted, style = MaterialTheme.typography.labelSmall)
                        Text(formatTime(duration), color = HexTextMuted, style = MaterialTheme.typography.labelSmall)
                    }
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly, verticalAlignment = Alignment.CenterVertically) {
                        IconButton(onClick = { prepare(if (selectedIndex == 0) playable.lastIndex else selectedIndex - 1) }, enabled = playable.size > 1) {
                            Icon(Icons.Outlined.SkipPrevious, "Previous", tint = HexCyan)
                        }
                        FilledIconButton(
                            onClick = {
                                if (playing) videoView.pause() else videoView.start()
                                playing = !playing
                            },
                            enabled = prepared,
                        ) { Icon(if (playing) Icons.Outlined.Pause else Icons.Outlined.PlayArrow, if (playing) "Pause" else "Play") }
                        IconButton(
                            onClick = { videoView.pause(); videoView.seekTo(0); playing = false; position = 0 },
                            enabled = prepared,
                        ) { Icon(Icons.Outlined.Stop, "Stop", tint = HexCyan) }
                        IconButton(onClick = { prepare(if (selectedIndex == playable.lastIndex) 0 else selectedIndex + 1) }, enabled = playable.size > 1) {
                            Icon(Icons.Outlined.SkipNext, "Next", tint = HexCyan)
                        }
                    }
                    error?.let { Text(it, color = HexCoral, style = MaterialTheme.typography.bodySmall) }
                }
            }
        }
        item { Text("COMPLETED MEDIA // TAP TO LOAD", color = HexCyan, style = MaterialTheme.typography.labelLarge) }
        items(playable, key = { it.request.id }) { item ->
            val index = playable.indexOf(item)
            val active = index == selectedIndex
            SystemPanel(Modifier.fillMaxWidth().clickable { prepare(index) }, if (active) HexMagenta else HexOutline) {
                Row(Modifier.padding(14.dp), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(if (item.request.format.name == "Mp4") Icons.Outlined.Movie else Icons.Outlined.AudioFile, null, tint = if (active) HexMagenta else HexCyan)
                    Column(Modifier.weight(1f)) {
                        Text("${item.request.format.label} // ${item.request.quality}", style = MaterialTheme.typography.labelLarge)
                        Text(item.request.url, maxLines = 1, overflow = TextOverflow.Ellipsis, color = HexTextMuted)
                    }
                    if (active) StatusPill("LOADED", HexMagenta)
                }
            }
        }
    }
}

private fun formatTime(milliseconds: Int): String {
    val seconds = milliseconds.coerceAtLeast(0) / 1000
    return "%02d:%02d".format(seconds / 60, seconds % 60)
}

internal fun playableItems(items: List<QueueItem>): List<QueueItem> =
    items.filter { it.state == DownloadState.Complete && !it.outputUri.isNullOrBlank() }
