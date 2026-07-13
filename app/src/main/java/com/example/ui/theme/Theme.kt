package com.example.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

private val PremiumDarkColorScheme = darkColorScheme(
    primary = PremiumPrimary,
    onPrimary = PremiumOnPrimary,
    primaryContainer = PremiumPrimaryContainer,
    onPrimaryContainer = PremiumOnPrimaryContainer,
    secondary = PremiumSecondary,
    onSecondary = PremiumOnSecondary,
    secondaryContainer = PremiumSecondaryContainer,
    onSecondaryContainer = PremiumOnSecondaryContainer,
    tertiary = PremiumTertiary,
    onTertiary = PremiumOnTertiary,
    background = PremiumBackground,
    surface = PremiumSurface,
    onBackground = PremiumOnBackground,
    onSurface = PremiumOnSurface,
    surfaceVariant = PremiumSurfaceVariant,
    onSurfaceVariant = PremiumOnSurfaceVariant,
    error = PremiumError,
    outline = PremiumOutline
)

enum class ThemeAccent(val label: String, val color: Color) {
    Bento("Neon Cyan", PremiumPrimary),
    Ocean("Electric Blue", Color(0xFF00B4DB)),
    Forest("Neon Green", Color(0xFF00FF87)),
    Sunset("Lava Red", Color(0xFFFF416C));

    companion object {
        fun fromLabel(label: String): ThemeAccent = entries.firstOrNull { it.label == label } ?: Bento
    }
}

@Composable
fun MyApplicationTheme(
    darkTheme: Boolean = true, // Force Dark Theme for the premium fintech aesthetic
    dynamicColor: Boolean = false, // Disable dynamic colors so our premium theme always applies
    accentColor: Color = PremiumPrimary,
    content: @Composable () -> Unit,
) {
    // We override primary colors with the selected accent, but keep the sleek dark background
    val colorScheme = PremiumDarkColorScheme.copy(
        primary = accentColor,
        primaryContainer = accentColor.copy(alpha = 0.2f)
    )

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography, // We can also update typography for a better look later
        content = content
    )
}
