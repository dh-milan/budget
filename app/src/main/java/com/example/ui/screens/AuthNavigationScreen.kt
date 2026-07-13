package com.example.ui.screens

import androidx.compose.animation.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import com.example.ui.theme.AnimationUtils
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
    var showSplash by remember { mutableStateOf(true) }
    var currentScreen by remember { mutableStateOf("login") } // login, register, forgot_password

    when {
        showSplash -> {
            SplashScreen(
                onSplashComplete = {
                    showSplash = false
                }
            )
        }
        isLoggedIn -> {
            // User is authenticated, show main app with fade in animation
            AnimatedVisibility(
                visible = true,
                enter = AnimationUtils.FadeIn + AnimationUtils.ScaleIn
            ) {
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
        }
        else -> {
            // Show authentication screens with animated transitions
            AnimatedContent(
                targetState = currentScreen,
                transitionSpec = {
                    when (targetState) {
                        "register" -> {
                            if (initialState == "login") {
                                slideInHorizontally { it } + fadeIn() togetherWith
                                        slideOutHorizontally { -it } + fadeOut()
                            } else {
                                slideInHorizontally { -it } + fadeIn() togetherWith
                                        slideOutHorizontally { it } + fadeOut()
                            }
                        }
                        "forgot_password" -> {
                            slideInVertically { it } + fadeIn() togetherWith
                                    slideOutVertically { -it } + fadeOut()
                        }
                        "login" -> {
                            slideInHorizontally { -it } + fadeIn() togetherWith
                                    slideOutHorizontally { it } + fadeOut()
                        }
                        else -> {
                            fadeIn() togetherWith fadeOut()
                        }
                    }.using(SizeTransform(clip = false))
                },
                label = "auth_screen_transition"
            ) { screen ->
                when (screen) {
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
}
