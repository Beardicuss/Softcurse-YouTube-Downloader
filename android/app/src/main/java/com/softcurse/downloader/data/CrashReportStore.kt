package com.softcurse.downloader.data

import android.content.Context
import android.os.Build
import com.softcurse.downloader.BuildConfig
import java.io.File
import java.time.Instant
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

class CrashReportStore(private val context: Context) {
    private val reportFile = File(context.filesDir, REPORT_FILE)
    private val _latestReport = MutableStateFlow(readReport())
    val latestReport: StateFlow<String?> = _latestReport

    fun capture(thread: Thread, error: Throwable) {
        val report = buildCrashReport(
            occurredAt = Instant.now().toString(),
            threadName = thread.name,
            error = error,
            appVersion = "${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})",
            androidVersion = "Android ${Build.VERSION.RELEASE} / API ${Build.VERSION.SDK_INT}",
            device = "${Build.MANUFACTURER} ${Build.MODEL}",
        ).take(MAX_REPORT_CHARS)
        runCatching {
            val temporary = File(context.filesDir, "$REPORT_FILE.tmp")
            temporary.writeText(report)
            if (!temporary.renameTo(reportFile)) {
                reportFile.writeText(report)
                temporary.delete()
            }
            _latestReport.value = report
        }
    }

    fun clear() {
        runCatching { reportFile.delete() }
        _latestReport.value = null
    }

    private fun readReport(): String? = runCatching {
        reportFile.takeIf(File::isFile)?.readText()?.takeIf(String::isNotBlank)
    }.getOrNull()

    companion object {
        const val SUPPORT_EMAIL = "softcursesystems@gmail.com"
        private const val REPORT_FILE = "latest-crash-report.txt"
        private const val MAX_REPORT_CHARS = 64 * 1024
    }
}

internal fun buildCrashReport(
    occurredAt: String,
    threadName: String,
    error: Throwable,
    appVersion: String,
    androidVersion: String,
    device: String,
): String = buildString {
    appendLine("Softcurse Systems Media Downloader crash report")
    appendLine("Generated locally; review before sending.")
    appendLine()
    appendLine("Occurred: $occurredAt")
    appendLine("App: $appVersion")
    appendLine("System: $androidVersion")
    appendLine("Device: $device")
    appendLine("Thread: $threadName")
    appendLine()
    appendLine(error.stackTraceToString())
}

internal fun supportDiagnosticSummary(): String = buildString {
    appendLine("App: Softcurse Systems Media Downloader ${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})")
    appendLine("System: Android ${Build.VERSION.RELEASE} / API ${Build.VERSION.SDK_INT}")
    appendLine("Device: ${Build.MANUFACTURER} ${Build.MODEL}")
}
