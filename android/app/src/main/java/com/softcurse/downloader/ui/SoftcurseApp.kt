package com.softcurse.downloader.ui

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.QueueMusic
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.softcurse.downloader.R
import com.softcurse.downloader.domain.DownloadState
import com.softcurse.downloader.ui.screens.*
import com.softcurse.downloader.ui.theme.*

private enum class Destination(val label: String, val code: String, val icon: ImageVector) {
    Download("Download", "DL", Icons.Outlined.Download),
    Queue("Queue", "Q", Icons.AutoMirrored.Outlined.QueueMusic),
    History("History", "HX", Icons.Outlined.History),
    Player("Player", "AV", Icons.Outlined.PlayCircle),
    Settings("Settings", "CFG", Icons.Outlined.Settings),
    About("About & Legal", "INFO", Icons.Outlined.Info),
}

private val primaryDestinations = Destination.entries.filter { it != Destination.About }

@Composable
fun SoftcurseApp(
    viewModelFactory: androidx.lifecycle.ViewModelProvider.Factory,
    notificationsAllowed: Boolean,
    onRequestNotifications: () -> Unit,
) {
    val viewModel: AppViewModel = androidx.lifecycle.viewmodel.compose.viewModel(factory = viewModelFactory)
    var destination by remember { mutableStateOf(Destination.Download) }
    val queue by viewModel.downloads.collectAsState()
    val history by viewModel.history.collectAsState()
    val settings by viewModel.settings.collectAsState()
    val downloadActive = queue.any { it.state == DownloadState.Pending || it.state == DownloadState.Running }

    BoxWithConstraints(Modifier.fillMaxSize().background(HexBackground)) {
        CircuitBoardBackground(downloadActive, settings.reducedMotion, Modifier.fillMaxSize())
        val wideLayout = maxWidth >= 720.dp
        Scaffold(
            containerColor = androidx.compose.ui.graphics.Color.Transparent,
            bottomBar = { if (!wideLayout) CommandDock(destination) { destination = it } },
        ) { insets ->
            Row(Modifier.fillMaxSize().padding(insets)) {
                if (wideLayout) CommandRail(destination) { destination = it }
                Column(
                    modifier = Modifier.fillMaxSize().padding(horizontal = if (wideLayout) 24.dp else 12.dp, vertical = 12.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    AppHeader(destination.label, settings.experimentalEngine, downloadActive)
                    Box(Modifier.fillMaxSize()) {
                        when (destination) {
                            Destination.Download -> DownloadScreen(settings.defaultFormat) { viewModel.enqueue(it.request); destination = Destination.Queue }
                            Destination.Queue -> QueueScreen(queue, viewModel::cancel, viewModel::delete)
                            Destination.History -> HistoryScreen(history, viewModel::retry)
                            Destination.Player -> PlayerScreen(history)
                            Destination.Settings -> SettingsScreen(settings, viewModel::setDefaultFormat, viewModel::setReducedMotion, viewModel::setWifiOnly, viewModel::setExperimentalEngine, notificationsAllowed, onRequestNotifications) { destination = Destination.About }
                            Destination.About -> AboutScreen { destination = Destination.Settings }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun CommandDock(selected: Destination, onSelect: (Destination) -> Unit) {
    Surface(color = Color.Transparent, border = BorderStroke(1.dp, HexCyan.copy(alpha = 0.28f)), shadowElevation = 18.dp) {
        Row(
            Modifier.fillMaxWidth().background(Brush.verticalGradient(listOf(HexSurfaceHigh.copy(alpha = 0.78f), HexSurface.copy(alpha = 0.62f)))).navigationBarsPadding().padding(horizontal = 4.dp, vertical = 5.dp),
            horizontalArrangement = Arrangement.SpaceEvenly,
        ) {
            primaryDestinations.forEach { item -> CommandItem(item, selected == item, Modifier.weight(1f)) { onSelect(item) } }
        }
    }
}

@Composable
private fun CommandRail(selected: Destination, onSelect: (Destination) -> Unit) {
    Surface(color = Color.Transparent, border = BorderStroke(1.dp, HexCyan.copy(alpha = 0.28f))) {
        Column(
            Modifier.width(92.dp).fillMaxHeight().background(Brush.horizontalGradient(listOf(HexSurfaceHigh.copy(alpha = 0.78f), HexSurface.copy(alpha = 0.58f)))).padding(vertical = 18.dp),
            verticalArrangement = Arrangement.Center,
        ) {
            primaryDestinations.forEach { item -> CommandItem(item, selected == item, Modifier.fillMaxWidth().padding(vertical = 6.dp)) { onSelect(item) } }
        }
    }
}

@Composable
private fun CommandItem(item: Destination, selected: Boolean, modifier: Modifier, onClick: () -> Unit) {
    val color = if (selected) HexCyan else HexTextMuted
    Column(
        modifier.clickable(onClick = onClick).padding(vertical = 7.dp, horizontal = 2.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(3.dp),
    ) {
        Box(
            Modifier.background(if (selected) HexCyan.copy(alpha = 0.14f) else androidx.compose.ui.graphics.Color.Transparent, CutCornerShape(5.dp)).padding(horizontal = 12.dp, vertical = 4.dp),
        ) { Icon(item.icon, item.label, tint = color, modifier = Modifier.size(21.dp)) }
        Text(item.code, color = color, style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp))
    }
}

@Composable
private fun AppHeader(section: String, experimentalEngine: Boolean, active: Boolean) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = Color.Transparent,
        border = BorderStroke(1.dp, if (active) HexSignalGreen.copy(alpha = 0.65f) else HexOutline),
        shape = CutCornerShape(topStart = 16.dp, bottomEnd = 16.dp),
        shadowElevation = 10.dp,
    ) {
        Row(
            Modifier.background(Brush.linearGradient(listOf(HexSurface.copy(alpha = 0.76f), HexSurface.copy(alpha = 0.52f), HexCyan.copy(alpha = 0.035f)))).padding(horizontal = 14.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Image(painterResource(R.drawable.softcurse_media_logo), "Softcurse Systems logo", Modifier.size(64.dp))
            Column(Modifier.weight(1f)) {
                Text("SOFTCURSE SYSTEMS", color = HexCyan, maxLines = 1, style = MaterialTheme.typography.headlineMedium.copy(fontSize = 18.sp, lineHeight = 21.sp))
                Text("MEDIA DOWNLOADER // ${section.uppercase()}", maxLines = 1, color = HexTextMuted, style = MaterialTheme.typography.labelLarge.copy(fontSize = 9.sp))
                Row(Modifier.padding(top = 6.dp), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    HeaderBadge(if (experimentalEngine) "ON-DEVICE POC" else "SIMULATED ENGINE", if (experimentalEngine) HexGold else HexCyan)
                    HeaderBadge(if (active) "NETWORK ACTIVE" else "SYSTEM IDLE", if (active) HexSignalGreen else HexCoral)
                }
            }
        }
    }
}

@Composable
private fun HeaderBadge(text: String, color: androidx.compose.ui.graphics.Color) {
    Text(text, color = color, modifier = Modifier.background(color.copy(alpha = 0.12f), CutCornerShape(4.dp)).padding(horizontal = 7.dp, vertical = 3.dp), style = MaterialTheme.typography.labelSmall.copy(fontSize = 8.sp))
}
