package com.example

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.ui.screens.*
import com.example.ui.theme.MyApplicationTheme
import com.example.ui.theme.ThemeAccent
import com.example.ui.viewmodel.FinanceViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            var darkThemeEnabled by rememberSaveable { mutableStateOf(false) }
            var dynamicColorEnabled by rememberSaveable { mutableStateOf(false) }
            var accentThemeName by rememberSaveable { mutableStateOf(ThemeAccent.Bento.name) }

            MyApplicationTheme(
                darkTheme = darkThemeEnabled,
                dynamicColor = dynamicColorEnabled,
                accentColor = ThemeAccent.valueOf(accentThemeName).color
            ) {
                val viewModel: FinanceViewModel = viewModel()
                AuthNavigationScreen(
                    viewModel = viewModel,
                    darkThemeEnabled = darkThemeEnabled,
                    onDarkThemeEnabledChange = { darkThemeEnabled = it },
                    dynamicColorEnabled = dynamicColorEnabled,
                    onDynamicColorEnabledChange = { dynamicColorEnabled = it },
                    accentThemeName = accentThemeName,
                    onAccentThemeNameChange = { accentThemeName = it }
                )
            }
        }
    }
}
