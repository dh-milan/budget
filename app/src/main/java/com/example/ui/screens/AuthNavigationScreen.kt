package com.example.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import com.example.ui.theme.AnimationUtils
import com.example.ui.viewmodel.AuthState
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
    val authState by viewModel.authState.collectAsState()
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
        authState is AuthState.Loading -> {
            // Show loading while checking session
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator(
                    color = MaterialTheme.colorScheme.primary
                )
            }
        }
        authState is AuthState.Authenticated -> {
            val user = (authState as AuthState.Authenticated).user
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
                    onAccentThemeNameChange = onAccentThemeNameChange,
                    userDisplayName = user.full_name,
                    userEmail = user.email,
                    onLogout = { viewModel.logout() }
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
                                // Auth state will be updated by ViewModel
                            },
                            onNavigateToRegister = {
                                currentScreen = "register"
                            },
                            onNavigateToForgotPassword = {
                                currentScreen = "forgot_password"
                            },
                            viewModel = viewModel
                        )
                    }
                    "register" -> {
                        RegisterScreen(
                            onRegisterSuccess = {
                                // Auth state will be updated by ViewModel
                            },
                            onNavigateToLogin = {
                                currentScreen = "login"
                            },
                            viewModel = viewModel
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