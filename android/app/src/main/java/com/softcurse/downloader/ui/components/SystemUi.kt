package com.softcurse.downloader.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.softcurse.downloader.ui.theme.HexCyan
import com.softcurse.downloader.ui.theme.HexOutline
import com.softcurse.downloader.ui.theme.HexSurface
import com.softcurse.downloader.ui.theme.HexTextMuted
import com.softcurse.downloader.ui.theme.HexText

@Composable
fun SystemPanel(
    modifier: Modifier = Modifier,
    accent: Color = HexCyan,
    darkGlass: Boolean = false,
    content: @Composable () -> Unit,
) {
    Surface(
        modifier = modifier,
        color = Color.Transparent,
        border = BorderStroke(1.dp, accent.copy(alpha = 0.58f)),
        shape = CutCornerShape(topStart = 14.dp, bottomEnd = 14.dp),
        shadowElevation = 10.dp,
    ) {
        Box(
            Modifier.background(
                Brush.linearGradient(
                    listOf(
                        HexSurface.copy(alpha = if (darkGlass) 0.88f else 0.64f),
                        HexSurface.copy(alpha = if (darkGlass) 0.72f else 0.42f),
                        accent.copy(alpha = if (darkGlass) 0.025f else 0.045f),
                    ),
                ),
            ),
        ) {
            content()
            Box(
                Modifier
                    .align(Alignment.TopStart)
                    .fillMaxWidth(0.18f)
                    .background(accent)
                    .padding(vertical = 1.dp),
            )
        }
    }
}

@Composable
fun SectionLead(kicker: String, title: String, detail: String) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(kicker.uppercase(), color = HexCyan, style = MaterialTheme.typography.labelLarge)
        Text(title, color = HexText, style = MaterialTheme.typography.titleLarge)
        Text(detail, color = HexTextMuted, style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
fun StatusPill(text: String, color: Color, modifier: Modifier = Modifier) {
    Box(
        modifier
            .background(color.copy(alpha = 0.12f), RoundedCornerShape(5.dp))
            .padding(horizontal = 8.dp, vertical = 4.dp),
    ) {
        Text(
            text.uppercase(),
            color = color,
            style = MaterialTheme.typography.labelLarge.copy(fontSize = 9.sp),
        )
    }
}

@Composable
fun MetricRow(content: @Composable RowScope.() -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        content = content,
    )
}

@Composable
fun RowScope.Metric(label: String, value: String, accent: Color = HexCyan) {
    Column(
        Modifier
            .weight(1f)
            .background(HexOutline.copy(alpha = 0.18f), RoundedCornerShape(7.dp))
            .padding(horizontal = 10.dp, vertical = 8.dp),
    ) {
        Text(label.uppercase(), color = HexTextMuted, style = MaterialTheme.typography.labelSmall)
        Text(value, color = accent, style = MaterialTheme.typography.labelLarge)
    }
}
