package com.softcurse.downloader.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.unit.dp
import com.softcurse.downloader.data.AppSettings
import com.softcurse.downloader.data.CrashReportStore
import com.softcurse.downloader.data.SupportClient
import com.softcurse.downloader.data.supportDiagnosticSummary
import com.softcurse.downloader.domain.MediaFormat
import com.softcurse.downloader.ui.components.*
import com.softcurse.downloader.ui.theme.*
import kotlinx.coroutines.launch

@Composable
fun SettingsScreen(
    settings: AppSettings,
    onDefaultFormat: (MediaFormat) -> Unit,
    onReducedMotion: (Boolean) -> Unit,
    onWifiOnly: (Boolean) -> Unit,
    onExperimentalEngine: (Boolean) -> Unit,
    notificationsAllowed: Boolean,
    onRequestNotifications: () -> Unit,
    crashReport: String?,
    onClearCrashReport: () -> Unit,
    onOpenAbout: () -> Unit,
) {
    val scope = rememberCoroutineScope()
    val supportClient = remember { SupportClient() }
    var writingSupport by remember { mutableStateOf(false) }
    var reviewingCrash by remember { mutableStateOf(false) }
    var sendingCrash by remember { mutableStateOf(false) }
    var submissionStatus by remember { mutableStateOf<String?>(null) }

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
        SystemPanel(Modifier.fillMaxWidth(), if (crashReport == null) HexCyan else HexGold) {
            Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("SUPPORT // LOCAL DIAGNOSTICS", color = if (crashReport == null) HexCyan else HexGold, style = MaterialTheme.typography.labelLarge)
                Text(
                    if (crashReport == null) "No saved crash report. Send a support message securely without leaving the app."
                    else "A crash report is stored privately on this device. Review it before choosing whether to send or delete it.",
                    color = HexTextMuted,
                )
                SelectionContainer {
                    Text(CrashReportStore.SUPPORT_EMAIL, color = HexTextMuted, style = MaterialTheme.typography.bodySmall)
                }
                OutlinedButton(
                    onClick = { writingSupport = true },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("WRITE TO SUPPORT") }
                if (crashReport != null) {
                    OutlinedButton(onClick = { reviewingCrash = true }, modifier = Modifier.fillMaxWidth()) {
                        Text("REVIEW CRASH REPORT")
                    }
                }
                submissionStatus?.let { Text(it, color = HexTextMuted, style = MaterialTheme.typography.bodySmall) }
            }
        }
    }

    if (writingSupport) {
        SupportMessageDialog(
            title = "Write to support",
            messageLabel = "How can we help?",
            initialMessage = "",
            diagnostics = supportDiagnosticSummary(),
            onDismiss = { writingSupport = false },
            onSend = { replyEmail, message, onFinished ->
                scope.launch {
                    runCatching {
                        supportClient.send(
                            type = "Support request",
                            subject = "Softcurse Media Downloader support",
                            message = message,
                            replyEmail = replyEmail,
                            diagnostics = supportDiagnosticSummary(),
                        )
                    }.onSuccess {
                        submissionStatus = "Support message sent."
                        writingSupport = false
                    }.onFailure {
                        submissionStatus = "Could not send. Check your connection and try again."
                    }
                    onFinished()
                }
            },
        )
    }

    if (sendingCrash && crashReport != null) {
        SupportMessageDialog(
            title = "Send crash report",
            messageLabel = "What were you doing before the crash?",
            initialMessage = "",
            diagnostics = crashReport,
            onDismiss = { sendingCrash = false },
            onSend = { replyEmail, message, onFinished ->
                scope.launch {
                    runCatching {
                        supportClient.send(
                            type = "Crash report",
                            subject = "Softcurse Media Downloader crash report",
                            message = message,
                            replyEmail = replyEmail,
                            diagnostics = crashReport,
                        )
                    }.onSuccess {
                        submissionStatus = "Crash report sent."
                        sendingCrash = false
                    }.onFailure {
                        submissionStatus = "Could not send. Check your connection and try again."
                    }
                    onFinished()
                }
            },
        )
    }

    if (reviewingCrash && crashReport != null) {
        AlertDialog(
            onDismissRequest = { reviewingCrash = false },
            title = { Text("Review crash report") },
            text = {
                SelectionContainer {
                    Text(crashReport, modifier = Modifier.heightIn(max = 420.dp).verticalScroll(rememberScrollState()))
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    reviewingCrash = false
                    sendingCrash = true
                }) { Text("SEND REPORT") }
            },
            dismissButton = {
                Row {
                    TextButton(onClick = {
                        onClearCrashReport()
                        reviewingCrash = false
                    }) { Text("DELETE") }
                    TextButton(onClick = { reviewingCrash = false }) { Text("CLOSE") }
                }
            },
        )
    }
}

@Composable
private fun SupportMessageDialog(
    title: String,
    messageLabel: String,
    initialMessage: String,
    diagnostics: String,
    onDismiss: () -> Unit,
    onSend: (String, String, () -> Unit) -> Unit,
) {
    var replyEmail by remember { mutableStateOf("") }
    var message by remember(initialMessage) { mutableStateOf(initialMessage) }
    var sending by remember { mutableStateOf(false) }
    AlertDialog(
        onDismissRequest = { if (!sending) onDismiss() },
        title = { Text(title) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedTextField(
                    value = replyEmail,
                    onValueChange = { replyEmail = it },
                    label = { Text("Your email (optional)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = message,
                    onValueChange = { message = it },
                    label = { Text(messageLabel) },
                    minLines = 5,
                    modifier = Modifier.fillMaxWidth(),
                )
                Text(
                    if (diagnostics.startsWith("Softcurse Systems Media Downloader crash report"))
                        "The crash report you reviewed will be included. Media URLs and queue contents are excluded."
                    else "Basic app and device diagnostics will be included. Media URLs and queue contents are excluded.",
                    color = HexTextMuted,
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        },
        confirmButton = {
            TextButton(
                enabled = message.isNotBlank() && !sending,
                onClick = {
                    sending = true
                    onSend(replyEmail.trim(), message.trim()) { sending = false }
                },
            ) { Text(if (sending) "SENDING…" else "SEND") }
        },
        dismissButton = { TextButton(enabled = !sending, onClick = onDismiss) { Text("CANCEL") } },
    )
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
