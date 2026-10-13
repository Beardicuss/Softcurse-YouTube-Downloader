package com.softcurse.downloader.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val HexBackground = Color(0xFF020202)
val HexSurface = Color(0xA8050810)
val HexSurfaceHigh = Color(0xFF0C1428)
val HexCyan = Color(0xFF00FFFF)
val HexSignalGreen = Color(0xFF6FD13E)
val HexMagenta = Color(0xFFFF00FF)
val HexCoral = Color(0xFFFF5B46)
val HexGold = Color(0xFFFF6B35)
val HexText = Color(0xFFE8F4F8)
val HexTextMuted = Color(0xFF83A8AE)
val HexOutline = Color(0xFF0D4A50)

private val SoftcurseColors = darkColorScheme(
    primary = HexCyan,
    onPrimary = HexBackground,
    secondary = HexMagenta,
    onSecondary = HexBackground,
    tertiary = HexGold,
    background = HexBackground,
    onBackground = HexText,
    surface = HexSurface,
    onSurface = HexText,
    surfaceVariant = HexSurfaceHigh,
    onSurfaceVariant = HexTextMuted,
    outline = HexOutline,
    error = HexCoral,
)

@Composable
fun SoftcurseTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = SoftcurseColors,
        typography = SoftcurseTypography,
        content = content,
    )
}
