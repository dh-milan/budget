package com.example.ui.theme

import android.os.Build
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.Modifier
import androidx.compose.ui.composed
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/**
 * Applies a Glassmorphism effect to a Composable.
 * Note: Background blur requires Android 12+ (API 31+). On older versions,
 * it gracefully degrades to a semi-transparent frosted glass look.
 */
fun Modifier.glassmorphism(
    cornerRadius: Dp = 16.dp,
    blurRadius: Dp = 20.dp,
    backgroundColor: Color = Color.White.copy(alpha = 0.15f),
    borderColor: Color = Color.White.copy(alpha = 0.4f),
    shape: Shape = RoundedCornerShape(cornerRadius),
    elevation: Dp = 4.dp
): Modifier = composed {
    this
        .shadow(elevation, shape, clip = false)
        .clip(shape)
        // Background blur effect
        .then(
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                Modifier.blur(radius = blurRadius)
            } else {
                Modifier
            }
        )
        .background(
            brush = Brush.linearGradient(
                colors = listOf(
                    backgroundColor,
                    backgroundColor.copy(alpha = backgroundColor.alpha * 0.5f)
                )
            )
        )
        .border(
            width = 1.dp,
            brush = Brush.linearGradient(
                colors = listOf(
                    borderColor,
                    borderColor.copy(alpha = 0.1f)
                )
            ),
            shape = shape
        )
}
