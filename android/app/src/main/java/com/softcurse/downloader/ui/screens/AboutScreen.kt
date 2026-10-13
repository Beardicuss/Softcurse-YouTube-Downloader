package com.softcurse.downloader.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.unit.dp
import com.softcurse.downloader.BuildConfig
import com.softcurse.downloader.ui.components.SectionLead
import com.softcurse.downloader.ui.components.StatusPill
import com.softcurse.downloader.ui.components.SystemPanel
import com.softcurse.downloader.ui.theme.HexCoral
import com.softcurse.downloader.ui.theme.HexCyan
import com.softcurse.downloader.ui.theme.HexGold
import com.softcurse.downloader.ui.theme.HexMagenta
import com.softcurse.downloader.ui.theme.HexSignalGreen
import com.softcurse.downloader.ui.theme.HexTextMuted

internal data class OpenSourceComponent(
    val name: String,
    val license: String,
    val sourceUrl: String,
    val note: String,
)

internal val openSourceComponents = listOf(
    OpenSourceComponent("AndroidX, Jetpack Compose & Material", "Apache License 2.0", "https://source.android.com/docs/setup/about/licenses", "UI, lifecycle, Room, DataStore and WorkManager foundations."),
    OpenSourceComponent("Kotlin", "Apache License 2.0", "https://github.com/JetBrains/kotlin", "Application language and coroutines runtime."),
    OpenSourceComponent("yt-dlp-android wrapper", "MIT License", "https://github.com/yausername/youtubedl-android", "Android extraction wrapper and embedded Python integration."),
    OpenSourceComponent("yt-dlp", "The Unlicense", "https://github.com/yt-dlp/yt-dlp", "Media information extraction and source download engine."),
    OpenSourceComponent("CPython", "Python Software Foundation License 2.0", "https://docs.python.org/3/license.html", "Embedded Python runtime used by the extraction engine."),
    OpenSourceComponent("FFmpegKit maintained audio build", "LGPL v3", "https://github.com/arthenica/ffmpeg-kit", "Non-GPL audio conversion package. This app does not use a GPL build."),
    OpenSourceComponent("FFmpeg", "LGPL v2.1 or later", "https://ffmpeg.org/legal.html", "Audio decoding and conversion libraries."),
    OpenSourceComponent("JUnit 4", "Eclipse Public License 1.0", "https://github.com/junit-team/junit4", "Development and unit testing only; not an app runtime feature."),
)

@Composable
fun AboutScreen(onBack: () -> Unit) {
    val uriHandler = LocalUriHandler.current
    Column(
        Modifier.verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        SectionLead("Release identity", "About & legal", "Transparent runtime, privacy, permissions, and open-source attribution.")

        SystemPanel(Modifier.fillMaxWidth(), HexCyan) {
            Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("SOFTCURSE SYSTEMS MEDIA DOWNLOADER", color = HexCyan, style = MaterialTheme.typography.titleMedium)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    StatusPill("VERSION ${BuildConfig.VERSION_NAME}", HexCyan)
                    StatusPill("BUILD ${BuildConfig.VERSION_CODE}", HexSignalGreen)
                }
                Text("Package: ${BuildConfig.APPLICATION_ID}", color = HexTextMuted)
                Text("Copyright © 2026 Softcurse Systems. Application code and branding remain subject to the project's own distribution terms.", color = HexTextMuted)
            }
        }

        LegalTextPanel(
            title = "PRIVACY // ON-DEVICE BY DEFAULT",
            accent = HexSignalGreen,
            paragraphs = listOf(
                "Effective 13 October 2026. The app has no account system, advertising, analytics, tracking, telemetry, or crash-reporting service.",
                "URLs, download state, history, output references, and preferences are stored locally on this device. Extraction and audio conversion run on-device.",
                "When you start a transfer, the app connects to the URL and services required by that source, which may include the source website or its media/CDN providers. Those services receive ordinary network information such as your IP address and are governed by their own policies.",
                "Completed files are written to Download/Softcurse through Android MediaStore. Uninstalling the app removes its private database and settings but does not automatically remove exported downloads.",
                "The app does not request broad storage access. Notification access is optional and is used only for background download status.",
            ),
        )

        LegalTextPanel(
            title = "PERMISSIONS // WHY THEY EXIST",
            accent = HexGold,
            paragraphs = listOf(
                "Internet — retrieve media selected by the user.",
                "Notifications — show foreground download progress on Android 13 and newer when authorized.",
                "Foreground service and foreground data sync — keep user-started transfers visible and reliable while the app is not in front.",
                "No contacts, location, camera, microphone, account, or broad media-library permission is requested.",
            ),
        )

        LegalTextPanel(
            title = "RESPONSIBLE USE",
            accent = HexCoral,
            paragraphs = listOf(
                "Download only media you own or are authorized to save. Website terms, copyright rules, and local law still apply.",
                "Softcurse Systems does not host media and cannot grant rights to third-party content. The user chooses every source and starts every transfer.",
            ),
        )

        SystemPanel(Modifier.fillMaxWidth(), HexMagenta) {
            Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("OPEN-SOURCE SOFTWARE", color = HexMagenta, style = MaterialTheme.typography.labelLarge)
                Text("The app includes the following projects. Select a source to review its complete license and notices.", color = HexTextMuted)
                openSourceComponents.forEach { component ->
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(component.name, style = MaterialTheme.typography.titleSmall)
                        Text(component.license, color = HexGold, style = MaterialTheme.typography.labelLarge)
                        Text(component.note, color = HexTextMuted, style = MaterialTheme.typography.bodySmall)
                        OutlinedButton(
                            modifier = Modifier.fillMaxWidth(),
                            onClick = { uriHandler.openUri(component.sourceUrl) },
                        ) { Text("VIEW SOURCE & LICENSE") }
                    }
                }
                Text("License names summarize the selected artifacts. Their upstream license texts and copyright notices control. This screen is not legal advice.", color = HexTextMuted, style = MaterialTheme.typography.bodySmall)
            }
        }

        OutlinedButton(onClick = onBack, modifier = Modifier.fillMaxWidth()) {
            Text("RETURN TO SETTINGS")
        }
    }
}

@Composable
private fun LegalTextPanel(title: String, accent: androidx.compose.ui.graphics.Color, paragraphs: List<String>) {
    SystemPanel(Modifier.fillMaxWidth(), accent) {
        Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text(title, color = accent, style = MaterialTheme.typography.labelLarge)
            paragraphs.forEach { paragraph ->
                Text(paragraph, color = HexTextMuted, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}
