package com.softcurse.downloader.ui

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import kotlin.math.floor
import com.softcurse.downloader.ui.theme.HexCoral
import com.softcurse.downloader.ui.theme.HexCyan
import com.softcurse.downloader.ui.theme.HexSignalGreen

@Composable
fun CircuitBoardBackground(
    active: Boolean,
    reducedMotion: Boolean,
    modifier: Modifier = Modifier,
) {
    val transition = rememberInfiniteTransition(label = "circuit-board")
    val activation by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(if (active) 2600 else 1900),
            repeatMode = if (active) RepeatMode.Restart else RepeatMode.Reverse,
        ),
        label = "circuit-activation",
    )
    val phase = if (reducedMotion) if (active) 1f else 0.35f else activation

    Canvas(modifier) {
        val grid = 40.dp.toPx()
        var x = 0f
        while (x <= size.width) {
            drawLine(HexCyan.copy(alpha = 0.05f), Offset(x, 0f), Offset(x, size.height), 1f)
            x += grid
        }
        var y = 0f
        while (y <= size.height) {
            drawLine(HexCyan.copy(alpha = 0.05f), Offset(0f, y), Offset(size.width, y), 1f)
            y += grid
        }

        val center = Offset(size.width * 0.54f, size.height * 0.52f)
        val endpoints = listOf(
            Offset(size.width * 0.08f, size.height * 0.18f),
            Offset(size.width * 0.28f, size.height * 0.30f),
            Offset(size.width * 0.82f, size.height * 0.20f),
            Offset(size.width * 0.93f, size.height * 0.39f),
            Offset(size.width * 0.12f, size.height * 0.62f),
            Offset(size.width * 0.31f, size.height * 0.82f),
            Offset(size.width * 0.76f, size.height * 0.76f),
            Offset(size.width * 0.92f, size.height * 0.88f),
        )
        val idle = HexCoral
        val live = HexSignalGreen
        val litCount = if (active) floor(phase * (endpoints.size + 1)).toInt() else -1

        endpoints.forEachIndexed { index, endpoint ->
            val isLit = active && index < litCount
            val color = if (isLit) live else idle
            val alpha = if (isLit) 0.62f else 0.10f + (if (!active && index == (phase * endpoints.size).toInt().coerceAtMost(7)) 0.20f else 0f)
            val midX = center.x + (endpoint.x - center.x) * 0.52f
            val path = Path().apply {
                moveTo(center.x, center.y)
                lineTo(midX, center.y)
                lineTo(midX, endpoint.y)
                lineTo(endpoint.x, endpoint.y)
            }
            drawPath(path, color.copy(alpha = alpha), style = Stroke(if (isLit) 3.dp.toPx() else 1.dp.toPx()))
            drawCircle(color.copy(alpha = alpha + 0.12f), if (isLit) 5.dp.toPx() else 3.dp.toPx(), endpoint)
            drawCircle(color.copy(alpha = alpha * 0.35f), if (isLit) 13.dp.toPx() else 8.dp.toPx(), endpoint)

            val tower = Size(22.dp.toPx(), 14.dp.toPx())
            drawRect(
                color.copy(alpha = alpha * 0.65f),
                topLeft = Offset(endpoint.x - tower.width / 2, endpoint.y - tower.height / 2),
                size = tower,
                style = Stroke(1.dp.toPx()),
            )
        }

        val chipSize = Size(90.dp.toPx(), 62.dp.toPx())
        val chipTopLeft = Offset(center.x - chipSize.width / 2, center.y - chipSize.height / 2)
        val chipColor = if (active) live else idle
        drawRect(chipColor.copy(alpha = if (active) 0.30f else 0.14f), chipTopLeft, chipSize, style = Stroke(2.dp.toPx()))
        drawRect(chipColor.copy(alpha = 0.05f), chipTopLeft, chipSize)
        repeat(6) { pin ->
            val py = chipTopLeft.y + (pin + 1) * chipSize.height / 7
            drawLine(chipColor.copy(alpha = 0.22f), Offset(chipTopLeft.x - 8.dp.toPx(), py), Offset(chipTopLeft.x, py), 2.dp.toPx())
            drawLine(chipColor.copy(alpha = 0.22f), Offset(chipTopLeft.x + chipSize.width, py), Offset(chipTopLeft.x + chipSize.width + 8.dp.toPx(), py), 2.dp.toPx())
        }
    }
}
