package com.example.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.CloudSync
import androidx.compose.material.icons.filled.DarkMode
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.Fingerprint
import androidx.compose.material.icons.filled.Language
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.Palette
import androidx.compose.material.icons.filled.PhoneAndroid
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Security
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Smartphone
import androidx.compose.material.icons.filled.Widgets
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedCard
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ui.theme.BentoAccentGold
import com.example.ui.theme.BentoAccentGreen
import com.example.ui.theme.BentoPrimary
import com.example.ui.theme.ThemeAccent

@Composable
fun ProductionSettingsScreen(
    onNavigateBack: () -> Unit,
    darkThemeEnabled: Boolean,
    onDarkThemeEnabledChange: (Boolean) -> Unit,
    dynamicColorEnabled: Boolean,
    onDynamicColorEnabledChange: (Boolean) -> Unit,
    accentThemeName: String,
    onAccentThemeNameChange: (String) -> Unit,
) {
    var notificationsEnabled by rememberSaveable { mutableStateOf(true) }
    var smartAlertsEnabled by rememberSaveable { mutableStateOf(true) }
    var offlineSyncEnabled by rememberSaveable { mutableStateOf(true) }
    var widgetsEnabled by rememberSaveable { mutableStateOf(true) }
    var biometricEnabled by rememberSaveable { mutableStateOf(false) }
    var currency by rememberSaveable { mutableStateOf("USD") }
    var language by rememberSaveable { mutableStateOf("English") }
    var fontStyle by rememberSaveable { mutableStateOf("Comfort") }
    var syncModeExpanded by remember { mutableStateOf(false) }
    var fontMenuExpanded by remember { mutableStateOf(false) }

    val accentTheme = ThemeAccent.fromLabel(accentThemeName)
    val productionReadyScore = listOf(
        darkThemeEnabled,
        notificationsEnabled,
        smartAlertsEnabled,
        offlineSyncEnabled,
        widgetsEnabled,
        biometricEnabled,
        accentTheme != ThemeAccent.Bento
    ).count { it }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .verticalScroll(rememberScrollState())
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    Brush.linearGradient(
                        colors = listOf(
                            accentTheme.color.copy(alpha = 0.95f),
                            BentoAccentGreen.copy(alpha = 0.85f),
                            BentoAccentGold.copy(alpha = 0.75f)
                        )
                    )
                )
                .padding(20.dp)
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    IconButton(onClick = onNavigateBack) {
                        Icon(
                            imageVector = Icons.Default.ArrowBack,
                            contentDescription = "Back",
                            tint = Color.White
                        )
                    }
                    Spacer(modifier = Modifier.weight(1f))
                    AssistChip(
                        onClick = { },
                        label = { Text("Production Ready", color = Color.White) },
                        leadingIcon = {
                            Icon(
                                imageVector = Icons.Default.CheckCircle,
                                contentDescription = null,
                                tint = Color.White,
                                modifier = Modifier.size(18.dp)
                            )
                        },
                        colors = AssistChipDefaults.assistChipColors(
                            containerColor = Color.White.copy(alpha = 0.18f),
                            labelColor = Color.White,
                            leadingIconContentColor = Color.White
                        ),
                        border = BorderStroke(1.dp, Color.White.copy(alpha = 0.2f))
                    )
                }

                Text(
                    text = "Settings",
                    fontSize = 30.sp,
                    fontWeight = FontWeight.ExtraBold,
                    color = Color.White
                )
                Text(
                    text = "Tune the app for polish, offline resilience, and production workflows.",
                    fontSize = 14.sp,
                    color = Color.White.copy(alpha = 0.92f),
                    lineHeight = 20.sp
                )

                OutlinedCard(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(22.dp),
                    colors = CardDefaults.outlinedCardColors(containerColor = Color.White.copy(alpha = 0.12f)),
                    border = BorderStroke(1.dp, Color.White.copy(alpha = 0.18f))
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            text = "Production checklist",
                            fontWeight = FontWeight.Bold,
                            color = Color.White,
                            fontSize = 14.sp
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            StatusPill("Theme", darkThemeEnabled)
                            StatusPill("Sync", offlineSyncEnabled)
                            StatusPill("Alerts", notificationsEnabled)
                            StatusPill("Widgets", widgetsEnabled)
                        }
                        Spacer(modifier = Modifier.height(10.dp))
                        Text(
                            text = "$productionReadyScore / 7 core toggles enabled",
                            fontSize = 12.sp,
                            color = Color.White.copy(alpha = 0.85f)
                        )
                    }
                }
            }
        }

        SettingsSectionHeader(title = "Appearance", subtitle = "Themes, colors, and typography")
        SettingsCard {
            SettingsToggleRow(
                icon = Icons.Default.DarkMode,
                title = "Dark mode",
                subtitle = "Use the high-contrast dark palette",
                checked = darkThemeEnabled,
                onCheckedChange = onDarkThemeEnabledChange
            )
            HorizontalDivider(color = MaterialTheme.colorScheme.outline.copy(alpha = 0.12f))
            SettingsToggleRow(
                icon = Icons.Default.Palette,
                title = "Dynamic color",
                subtitle = "Adopt system colors when available",
                checked = dynamicColorEnabled,
                onCheckedChange = onDynamicColorEnabledChange
            )
            HorizontalDivider(color = MaterialTheme.colorScheme.outline.copy(alpha = 0.12f))
            Column(modifier = Modifier.padding(vertical = 12.dp)) {
                Text(
                    text = "Accent color",
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onSurface,
                    fontSize = 15.sp
                )
                Text(
                    text = "Pick a brand tone for the app shell",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    fontSize = 12.sp,
                    modifier = Modifier.padding(top = 2.dp)
                )
                Spacer(modifier = Modifier.height(12.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    ThemeAccent.entries.forEach { option ->
                        FilterChip(
                            selected = accentTheme == option,
                            onClick = { onAccentThemeNameChange(option.name) },
                            label = { Text(option.label) },
                            leadingIcon = {
                                Box(
                                    modifier = Modifier
                                        .size(12.dp)
                                        .clip(CircleShape)
                                        .background(option.color)
                                )
                            },
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = option.color.copy(alpha = 0.18f),
                                selectedLabelColor = option.color,
                                selectedLeadingIconColor = option.color
                            )
                        )
                    }
                }
                Spacer(modifier = Modifier.height(12.dp))
                TextButton(onClick = { fontMenuExpanded = true }) {
                    Text("Font style: $fontStyle")
                    Icon(imageVector = Icons.Default.Refresh, contentDescription = null)
                }
                DropdownMenu(expanded = fontMenuExpanded, onDismissRequest = { fontMenuExpanded = false }) {
                    listOf("Comfort", "Compact", "Display").forEach { option ->
                        DropdownMenuItem(
                            text = { Text(option) },
                            onClick = {
                                fontStyle = option
                                fontMenuExpanded = false
                            }
                        )
                    }
                }
            }
        }

        SettingsSectionHeader(title = "Offline Support", subtitle = "Background sync and conflict handling")
        SettingsCard {
            SettingsToggleRow(
                icon = Icons.Default.CloudSync,
                title = "Offline-first sync",
                subtitle = "Queue changes locally until the network returns",
                checked = offlineSyncEnabled,
                onCheckedChange = { offlineSyncEnabled = it }
            )
            HorizontalDivider(color = MaterialTheme.colorScheme.outline.copy(alpha = 0.12f))
            SettingsMenuRow(
                icon = Icons.Default.Refresh,
                title = "Sync mode",
                subtitle = if (offlineSyncEnabled) "Delta sync, retry queue, conflict resolution" else "Sync paused"
            ) {
                syncModeExpanded = true
            }
            DropdownMenu(
                expanded = syncModeExpanded,
                onDismissRequest = { syncModeExpanded = false }
            ) {
                listOf("Automatic", "Manual", "Wi-Fi only").forEach { option ->
                    DropdownMenuItem(
                        text = { Text(option) },
                        onClick = { syncModeExpanded = false }
                    )
                }
            }
        }

        SettingsSectionHeader(title = "Notifications", subtitle = "Smart alerts and reminders")
        SettingsCard {
            SettingsToggleRow(
                icon = Icons.Default.Notifications,
                title = "Push notifications",
                subtitle = "Bills, savings goals, and security alerts",
                checked = notificationsEnabled,
                onCheckedChange = { notificationsEnabled = it }
            )
            HorizontalDivider(color = MaterialTheme.colorScheme.outline.copy(alpha = 0.12f))
            SettingsToggleRow(
                icon = Icons.Default.Security,
                title = "Smart alerts",
                subtitle = "Budget warnings and goal milestones",
                checked = smartAlertsEnabled,
                onCheckedChange = { smartAlertsEnabled = it }
            )
            HorizontalDivider(color = MaterialTheme.colorScheme.outline.copy(alpha = 0.12f))
            SettingsToggleRow(
                icon = Icons.Default.Fingerprint,
                title = "Biometric login",
                subtitle = "Unlock the app using the device secure hardware",
                checked = biometricEnabled,
                onCheckedChange = { biometricEnabled = it }
            )
        }

        SettingsSectionHeader(title = "Widgets", subtitle = "Balance and budget glance cards")
        SettingsCard {
            SettingsToggleRow(
                icon = Icons.Default.Widgets,
                title = "Widget suite",
                subtitle = "Enable balance, budget, and bills widgets",
                checked = widgetsEnabled,
                onCheckedChange = { widgetsEnabled = it }
            )
            Spacer(modifier = Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                AssistChip(onClick = { }, label = { Text("Balance") })
                AssistChip(onClick = { }, label = { Text("Budget") })
                AssistChip(onClick = { }, label = { Text("Bills") })
            }
        }

        SettingsSectionHeader(title = "Regional", subtitle = "Currency and language")
        SettingsCard {
            SettingsMenuRow(
                icon = Icons.Default.Smartphone,
                title = "Currency",
                subtitle = currency
            ) {
                currency = when (currency) {
                    "USD" -> "EUR"
                    "EUR" -> "GBP"
                    "GBP" -> "INR"
                    "INR" -> "JPY"
                    "JPY" -> "USD"
                    else -> "USD"
                }
            }
            HorizontalDivider(color = MaterialTheme.colorScheme.outline.copy(alpha = 0.12f))
            SettingsMenuRow(
                icon = Icons.Default.Language,
                title = "Language",
                subtitle = language
            ) {
                language = when (language) {
                    "English" -> "Spanish"
                    "Spanish" -> "French"
                    "French" -> "German"
                    "German" -> "English"
                    else -> "English"
                }
            }
        }

        SettingsSectionHeader(title = "Data & Devices", subtitle = "Backup, export, and security")
        SettingsCard {
            SettingsMenuRow(
                icon = Icons.Default.Download,
                title = "Backup data",
                subtitle = "Snapshot your local data and settings"
            ) { }
            HorizontalDivider(color = MaterialTheme.colorScheme.outline.copy(alpha = 0.12f))
            SettingsMenuRow(
                icon = Icons.Default.Settings,
                title = "Device management",
                subtitle = "Trusted devices and session history"
            ) { }
            HorizontalDivider(color = MaterialTheme.colorScheme.outline.copy(alpha = 0.12f))
            SettingsMenuRow(
                icon = Icons.Default.PhoneAndroid,
                title = "App storage",
                subtitle = "Clear cache and review local storage"
            ) { }
        }

        Spacer(modifier = Modifier.height(24.dp))
    }
}

@Composable
private fun SettingsSectionHeader(title: String, subtitle: String) {
    Column(modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp)) {
        Text(
            text = title,
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary,
            letterSpacing = 1.sp
        )
        Text(
            text = subtitle,
            fontSize = 13.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 4.dp)
        )
    }
}

@Composable
private fun SettingsCard(content: @Composable androidx.compose.foundation.layout.ColumnScope.() -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp),
        shape = RoundedCornerShape(22.dp),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.08f)),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column(modifier = Modifier.padding(16.dp), content = content)
    }
}

@Composable
private fun SettingsToggleRow(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    title: String,
    subtitle: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(44.dp)
                .clip(RoundedCornerShape(14.dp))
                .background(MaterialTheme.colorScheme.primaryContainer),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = title,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(22.dp)
            )
        }
        Spacer(modifier = Modifier.size(16.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                fontSize = 15.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurface
            )
            Text(
                text = subtitle,
                fontSize = 12.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 2.dp)
            )
        }
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange,
            colors = SwitchDefaults.colors(
                checkedThumbColor = MaterialTheme.colorScheme.primary,
                checkedTrackColor = MaterialTheme.colorScheme.primaryContainer
            )
        )
    }
}

@Composable
private fun SettingsMenuRow(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    title: String,
    subtitle: String,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(44.dp)
                .clip(RoundedCornerShape(14.dp))
                .background(MaterialTheme.colorScheme.primaryContainer),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = title,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(22.dp)
            )
        }
        Spacer(modifier = Modifier.size(16.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                fontSize = 15.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurface
            )
            Text(
                text = subtitle,
                fontSize = 12.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 2.dp)
            )
        }
        OutlinedButton(
            onClick = onClick,
            contentPadding = PaddingValues(horizontal = 14.dp, vertical = 10.dp)
        ) {
            Text("Edit")
        }
    }
}

@Composable
private fun StatusPill(label: String, active: Boolean) {
    val background = if (active) Color.White.copy(alpha = 0.18f) else Color.Black.copy(alpha = 0.12f)
    val border = if (active) Color.White.copy(alpha = 0.22f) else Color.Black.copy(alpha = 0.10f)
    val content = if (active) Color.White else MaterialTheme.colorScheme.onSurfaceVariant

    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(999.dp))
            .background(background)
            .padding(horizontal = 10.dp, vertical = 6.dp)
    ) {
        Text(
            text = label,
            color = content,
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold
        )
    }
}
