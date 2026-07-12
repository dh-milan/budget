package com.example.ui.screens

import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import com.example.ui.viewmodel.FinanceViewModel

@Composable
fun AuthNavigationScreen(
    viewModel: FinanceViewModel,
    darkThemeEnabled: Boolean,
    onDarkThemeEnabledChange: (Boolean) -> Unit,
    dynamicColorEnabled: Boolean,
    onDynamicColorEnabledChange: (Boolean) -> Unit,
    accentThemeName: String,
    onAccentThemeNameChange: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    var isLoggedIn by remember { mutableStateOf(false) }
    var currentScreen by remember { mutableStateOf("login") } // login, register, forgot_password

    when {
        isLoggedIn -> {
            // User is authenticated, show main app
            MainAppScreen(
                viewModel = viewModel,
                darkThemeEnabled = darkThemeEnabled,
                onDarkThemeEnabledChange = onDarkThemeEnabledChange,
                dynamicColorEnabled = dynamicColorEnabled,
                onDynamicColorEnabledChange = onDynamicColorEnabledChange,
                accentThemeName = accentThemeName,
                onAccentThemeNameChange = onAccentThemeNameChange
            )
        }
        else -> {
            // Show authentication screens
            when (currentScreen) {
                "login" -> {
                    LoginScreen(
                        onLoginSuccess = {
                            isLoggedIn = true
                        },
                        onNavigateToRegister = {
                            currentScreen = "register"
                        },
                        onNavigateToForgotPassword = {
                            currentScreen = "forgot_password"
                        }
                    )
                }
                "register" -> {
                    RegisterScreen(
                        onRegisterSuccess = {
                            isLoggedIn = true
                        },
                        onNavigateToLogin = {
                            currentScreen = "login"
                        }
                    )
                }
                "forgot_password" -> {
                    ForgotPasswordScreen(
                        onNavigateBack = {
                            currentScreen = "login"
                        }
                    )
                }
            }
        }
    }
}