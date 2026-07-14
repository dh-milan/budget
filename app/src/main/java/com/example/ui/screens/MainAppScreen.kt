package com.example.ui.screens

import android.widget.Toast
import androidx.activity.compose.BackHandler
import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.automirrored.filled.ReceiptLong
import androidx.compose.material.icons.automirrored.outlined.Chat
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import kotlinx.coroutines.delay
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.example.R
import com.example.data.model.*
import com.example.ui.theme.*
import com.example.ui.theme.AnimationUtils
import com.example.ui.viewmodel.FinanceViewModel
import java.text.SimpleDateFormat
import java.util.*
import kotlin.time.Duration.Companion.milliseconds

sealed class ScreenTab(val title: String, val icon: ImageVector) {
    object Dashboard : ScreenTab("Insights", Icons.Default.Dashboard)
    object Transactions : ScreenTab("Ledger", Icons.AutoMirrored.Filled.ReceiptLong)
    object Budgets : ScreenTab("Budgets", Icons.Default.PieChart)
    object Bills : ScreenTab("Bills & Debt", Icons.Default.CreditCard)
    object Analytics : ScreenTab("Analytics", Icons.Default.Analytics)
    object Profile : ScreenTab("Profile", Icons.Default.Person)
    object Assistant : ScreenTab("AI Advisor", Icons.AutoMirrored.Outlined.Chat)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainAppScreen(
    viewModel: FinanceViewModel,
    darkThemeEnabled: Boolean,
    onDarkThemeEnabledChange: (Boolean) -> Unit,
    dynamicColorEnabled: Boolean,
    onDynamicColorEnabledChange: (Boolean) -> Unit,
    accentThemeName: String,
    onAccentThemeNameChange: (String) -> Unit,
    userDisplayName: String = "User",
    userEmail: String = "user@example.com",
    onLogout: () -> Unit = {}
) {
    val context = LocalContext.current
    val clipboardManager = LocalClipboardManager.current

    // Trigger initial prepopulated data
    LaunchedEffect(Unit) {
        viewModel.prepopulateData()
    }

    // States
    var currentTab by remember { mutableStateOf<ScreenTab>(ScreenTab.Dashboard) }
    var showSettingsScreen by remember { mutableStateOf(false) }
    var showAddTxDialog by remember { mutableStateOf(false) }
    var showAddBudgetDialog by remember { mutableStateOf(false) }
    var showAddGoalDialog by remember { mutableStateOf(false) }
    var showAddDebtDialog by remember { mutableStateOf(false) }
    var showAddBillDialog by remember { mutableStateOf(false) }

    val transactions by viewModel.transactions.collectAsStateWithLifecycle()
    val budgets by viewModel.budgets.collectAsStateWithLifecycle()
    val goals by viewModel.goals.collectAsStateWithLifecycle()
    val debts by viewModel.debts.collectAsStateWithLifecycle()
    val bills by viewModel.bills.collectAsStateWithLifecycle()

    BackHandler(enabled = showSettingsScreen) {
        showSettingsScreen = false
    }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .size(28.dp)
                                .clip(CircleShape)
                                .background(Brush.horizontalGradient(listOf(BentoPrimary, BentoSecondary)))
                        )
                        Text(
                            text = "WEALTH FLOW",
                            fontSize = 16.sp,
                            fontWeight = FontWeight.ExtraBold,
                            letterSpacing = 1.5.sp,
                            color = MaterialTheme.colorScheme.onBackground
                        )
                    }
                },
                actions = {
                    IconButton(
                        onClick = {
                            val csvData = viewModel.exportToCsv()
                            clipboardManager.setText(AnnotatedString(csvData))
                            Toast.makeText(context, "Ledger exported to clipboard as CSV", Toast.LENGTH_LONG).show()
                        },
                        modifier = Modifier.testTag("export_csv_button")
                    ) {
                        Icon(
                            imageVector = Icons.Default.Share,
                            contentDescription = "Export CSV",
                            tint = MaterialTheme.colorScheme.onBackground
                        )
                    }
                },
                colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background
                )
            )
        },
        bottomBar = {
            NavigationBar(
                containerColor = MaterialTheme.colorScheme.surface,
                tonalElevation = 8.dp
            ) {
                val tabs = listOf(
                    ScreenTab.Dashboard,
                    ScreenTab.Transactions,
                    ScreenTab.Budgets,
                    ScreenTab.Bills,
                    ScreenTab.Analytics,
                    ScreenTab.Profile,
                    ScreenTab.Assistant
                )
                tabs.forEach { tab ->
                    NavigationBarItem(
                        selected = currentTab == tab,
                        onClick = { currentTab = tab },
                        icon = { Icon(tab.icon, contentDescription = tab.title) },
                        alwaysShowLabel = false,
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = MaterialTheme.colorScheme.primary,
                            indicatorColor = MaterialTheme.colorScheme.primaryContainer,
                            unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f)
                        ),
                        modifier = Modifier.testTag("nav_tab_${tab.title.lowercase()}")
                    )
                }
            }
        },
        floatingActionButton = {
            if (currentTab != ScreenTab.Assistant) {
                var fabScale by remember { mutableFloatStateOf(1f) }
                
                ExtendedFloatingActionButton(
                    onClick = {
                        // Pulse animation on click
                        fabScale = 0.9f
                        
                        when (currentTab) {
                            ScreenTab.Dashboard -> showAddTxDialog = true
                            ScreenTab.Transactions -> showAddTxDialog = true
                            ScreenTab.Budgets -> showAddBudgetDialog = true
                            ScreenTab.Bills -> showAddBillDialog = true
                            ScreenTab.Analytics -> {}
                            ScreenTab.Profile -> {}
                            ScreenTab.Assistant -> {}
                        }
                    },
                    containerColor = MaterialTheme.colorScheme.primary,
                    contentColor = MaterialTheme.colorScheme.onPrimary,
                    icon = { Icon(Icons.Default.Add, contentDescription = "Create New") },
                    text = {
                        Text(
                            text = when (currentTab) {
                                ScreenTab.Dashboard, ScreenTab.Transactions -> "Add Tx"
                                ScreenTab.Budgets -> "New Budget"
                                ScreenTab.Bills -> "New Bill"
                                ScreenTab.Analytics -> "Report"
                                ScreenTab.Profile -> ""
                                ScreenTab.Assistant -> "Ask AI"
                            }
                        )
                    },
                    modifier = Modifier
                        .testTag("fab_add_action")
                        .scale(fabScale)
                )
                // Animate back to normal scale - optimized
                LaunchedEffect(fabScale) {
                    if (fabScale != 1f) {
                        delay(100)
                        fabScale = 1f
                    }
                }
            }
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            if (showSettingsScreen) {
                AnimatedVisibility(
                    visible = showSettingsScreen,
                    enter = AnimationUtils.SlideInFromRight + AnimationUtils.FadeIn,
                    exit = AnimationUtils.SlideOutToLeft + AnimationUtils.FadeOut
                ) {
                    ProductionSettingsScreen(
                        onNavigateBack = { showSettingsScreen = false },
                        darkThemeEnabled = darkThemeEnabled,
                        onDarkThemeEnabledChange = onDarkThemeEnabledChange,
                        dynamicColorEnabled = dynamicColorEnabled,
                        onDynamicColorEnabledChange = onDynamicColorEnabledChange,
                        accentThemeName = accentThemeName,
                        onAccentThemeNameChange = onAccentThemeNameChange
                    )
                }
            } else {
                Crossfade(
                    targetState = currentTab,
                    animationSpec = tween(AnimationUtils.NORMAL_DURATION, easing = AnimationUtils.NormalEaseOut),
                    label = "TabTransition"
                ) { tab ->
                    when (tab) {
                    ScreenTab.Dashboard -> DashboardScreenView(
                        transactions = transactions,
                        onAddTxClick = { showAddTxDialog = true },
                        userDisplayName = userDisplayName
                    )
                    ScreenTab.Transactions -> TransactionsScreenView(
                        transactions = transactions,
                        onDeleteTransaction = { id, amt, cat, type ->
                            viewModel.deleteTransaction(id, amt, cat, type)
                        }
                    )
                    ScreenTab.Budgets -> BudgetsScreenView(
                        budgets = budgets,
                        goals = goals,
                        onAddBudget = { showAddBudgetDialog = true },
                        onAddGoal = { showAddGoalDialog = true },
                        onDeleteBudget = { viewModel.deleteBudget(it) },
                        onDeleteGoal = { viewModel.deleteGoal(it) },
                        onContributeGoal = { id, amt -> viewModel.contributeToGoal(id, amt) }
                    )
                    ScreenTab.Bills -> BillsScreenView(
                        bills = bills,
                        debts = debts,
                        onPayBill = { viewModel.markBillAsPaid(it) },
                        onDeleteBill = { viewModel.deleteBill(it) },
                        onPayDebt = { id, amt -> viewModel.payDebt(id, amt) },
                        onAddDebtClick = { showAddDebtDialog = true },
                        onDeleteDebt = { viewModel.deleteDebt(it) }
                    )
                    ScreenTab.Analytics -> AnalyticsScreenView(
                        transactions = transactions,
                        budgets = budgets,
                        goals = goals
                    )
                    ScreenTab.Profile -> ProfileScreen(
                        onNavigateToSettings = { showSettingsScreen = true },
                        onLogout = onLogout,
                        userDisplayName = userDisplayName,
                        userEmail = userEmail,
                        viewModel = viewModel
                    )
                    ScreenTab.Assistant -> AssistantScreenView(viewModel)
                }
            }
        }
    }
}

    // Dialogs with animations
    if (showAddTxDialog) {
        AnimatedVisibility(
            visible = showAddTxDialog,
            enter = AnimationUtils.FadeIn + AnimationUtils.ScaleIn,
            exit = AnimationUtils.FadeOut + AnimationUtils.ScaleOut
        ) {
            AddTransactionDialog(
                onDismiss = { showAddTxDialog = false },
                onConfirm = { title, amount, category, type, note, tags ->
                    viewModel.addTransaction(title, amount, category, type, note, tags)
                    showAddTxDialog = false
                }
            )
        }
    }

    if (showAddBudgetDialog) {
        AnimatedVisibility(
            visible = showAddBudgetDialog,
            enter = AnimationUtils.FadeIn + AnimationUtils.ScaleIn,
            exit = AnimationUtils.FadeOut + AnimationUtils.ScaleOut
        ) {
            AddBudgetDialog(
                onDismiss = { showAddBudgetDialog = false },
                onConfirm = { category, limit ->
                    viewModel.addBudget(category, limit)
                    showAddBudgetDialog = false
                }
            )
        }
    }

    if (showAddGoalDialog) {
        AnimatedVisibility(
            visible = showAddGoalDialog,
            enter = AnimationUtils.FadeIn + AnimationUtils.ScaleIn,
            exit = AnimationUtils.FadeOut + AnimationUtils.ScaleOut
        ) {
            AddGoalDialog(
                onDismiss = { showAddGoalDialog = false },
                onConfirm = { name, target, current ->
                    viewModel.addGoal(name, target, current, System.currentTimeMillis() + (30L * 24 * 60 * 60 * 1000))
                    showAddGoalDialog = false
                }
            )
        }
    }

    if (showAddDebtDialog) {
        AnimatedVisibility(
            visible = showAddDebtDialog,
            enter = AnimationUtils.FadeIn + AnimationUtils.ScaleIn,
            exit = AnimationUtils.FadeOut + AnimationUtils.ScaleOut
        ) {
            AddDebtDialog(
                onDismiss = { showAddDebtDialog = false },
                onConfirm = { name, type, total, interest, payment ->
                    viewModel.addDebt(name, type, total, interest, System.currentTimeMillis() + (30L * 24 * 60 * 60 * 1000), payment)
                    showAddDebtDialog = false
                }
            )
        }
    }

    if (showAddBillDialog) {
        AnimatedVisibility(
            visible = showAddBillDialog,
            enter = AnimationUtils.FadeIn + AnimationUtils.ScaleIn,
            exit = AnimationUtils.FadeOut + AnimationUtils.ScaleOut
        ) {
            AddBillDialog(
                onDismiss = { showAddBillDialog = false },
                onConfirm = { name, amount, category ->
                    viewModel.addBill(name, amount, System.currentTimeMillis() + (15L * 24 * 60 * 60 * 1000), category)
                    showAddBillDialog = false
                }
            )
        }
    }
}

// ==================== DASHBOARD VIEW ====================

@Composable
fun DashboardScreenView(
    transactions: List<TransactionEntity>,
    onAddTxClick: () -> Unit,
    userDisplayName: String = "User"
) {
    val totalIncome = transactions.filter { it.type == "INCOME" }.sumOf { it.amount }
    val totalExpense = transactions.filter { it.type == "EXPENSE" }.sumOf { it.amount }
    val netWorth = totalIncome - totalExpense
    val initials = userDisplayName.split(" ").map { it.firstOrNull()?.uppercase() ?: "" }.take(2).joinToString("")

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Premium Greeting Header Item (Bento Style)
        item {
            AnimatedVisibility(
                visible = true,
                enter = AnimationUtils.SlideInFromBottom + AnimationUtils.FadeIn
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 4.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = "Good ${getGreeting()},",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Medium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                        )
                        Text(
                            text = userDisplayName,
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onBackground
                        )
                    }
                    Box(
                        modifier = Modifier
                            .size(40.dp)
                            .clip(CircleShape)
                            .background(MaterialTheme.colorScheme.primaryContainer)
                            .clickable { /* Profile details */ },
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = initials.ifEmpty { "U" },
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                    }
                }
            }
        }

        // Hero Card
        item {
            AnimatedVisibility(
                visible = true,
                enter = AnimationUtils.SlideInFromBottom + AnimationUtils.FadeIn
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(180.dp)
                        .clip(RoundedCornerShape(28.dp))
                        .background(
                            Brush.verticalGradient(
                                listOf(
                                    MaterialTheme.colorScheme.primary,
                                    MaterialTheme.colorScheme.secondary
                                )
                            )
                        )
                ) {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(20.dp),
                    verticalArrangement = Arrangement.SpaceBetween
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "NET WORTH",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color.White.copy(alpha = 0.8f),
                            letterSpacing = 1.5.sp
                        )
                        if (totalIncome > 0) {
                            val changePercent = if (totalIncome > 0) ((totalIncome - totalExpense) / totalIncome * 100) else 0.0
                            Box(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(12.dp))
                                    .background(Color.White.copy(alpha = 0.2f))
                                    .padding(horizontal = 8.dp, vertical = 4.dp)
                            ) {
                                Text(
                                    text = "${if (changePercent >= 0) "+" else ""}${String.format("%.1f", changePercent)}%",
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color.White
                                )
                            }
                        }
                    }
                    Column {
                        Text(
                            text = "$${String.format(Locale.US, "%,.2f", netWorth)}",
                            fontSize = 32.sp,
                            fontWeight = FontWeight.Black,
                            color = Color.White
                        )
                        Row(
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                            modifier = Modifier.padding(top = 4.dp)
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.ArrowUpward, contentDescription = "Income", tint = Color(0xFF81C784), modifier = Modifier.size(12.dp))
                                Text(text = " +$${String.format(Locale.US, "%,.0f", totalIncome)}", fontSize = 11.sp, color = Color(0xFF81C784))
                            }
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.ArrowDownward, contentDescription = "Expense", tint = Color(0xFFE57373), modifier = Modifier.size(12.dp))
                                Text(text = " -$${String.format(Locale.US, "%,.0f", totalExpense)}", fontSize = 11.sp, color = Color(0xFFE57373))
                            }
                        }
                    }
                }
            }
            }
        }

        // Summary Cards Row
        item {
            AnimatedVisibility(
                visible = true,
                enter = AnimationUtils.SlideInFromBottom + AnimationUtils.FadeIn
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    SummaryCard(
                        title = "Income",
                        value = "$${String.format(Locale.US, "%,.0f", totalIncome)}",
                        icon = Icons.Default.TrendingUp,
                        color = BentoAccentGreen,
                        modifier = Modifier.weight(1f)
                    )
                    SummaryCard(
                        title = "Expenses",
                        value = "$${String.format(Locale.US, "%,.0f", totalExpense)}",
                        icon = Icons.Default.TrendingDown,
                        color = BentoError,
                        modifier = Modifier.weight(1f)
                    )
                }
            }
        }

        // AI Financial Insight (only if there's data)
        if (transactions.isNotEmpty()) {
            item {
                AnimatedVisibility(
                    visible = true,
                    enter = AnimationUtils.SlideInFromBottom + AnimationUtils.FadeIn
                ) {
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.primaryContainer
                        ),
                        shape = RoundedCornerShape(24.dp),
                        border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.2f)),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            modifier = Modifier
                                .size(42.dp)
                                .clip(RoundedCornerShape(16.dp))
                                .background(MaterialTheme.colorScheme.primary),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                imageVector = Icons.Default.TipsAndUpdates,
                                contentDescription = "Insights",
                                tint = MaterialTheme.colorScheme.onPrimary
                            )
                        }
                        Spacer(modifier = Modifier.width(16.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = "FINANCIAL INSIGHT",
                                fontSize = 10.sp,
                                fontWeight = FontWeight.ExtraBold,
                                color = MaterialTheme.colorScheme.primary,
                                letterSpacing = 1.2.sp
                            )
                            Spacer(modifier = Modifier.height(2.dp))
                            Text(
                                text = if (netWorth > 0) {
                                    "Your cash flow is positive. Consider allocating 20% to savings goals."
                                } else {
                                    "Expenses exceed income this period. Review your budget to identify savings opportunities."
                                },
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Medium,
                                color = MaterialTheme.colorScheme.onPrimaryContainer,
                                lineHeight = 16.sp
                            )
                        }
                    }
                }
                }
            }
        }

        // Recent Activity Header Title
        item {
            AnimatedVisibility(
                visible = true,
                enter = AnimationUtils.SlideInFromBottom + AnimationUtils.FadeIn
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Recent Transactions",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onBackground
                    )
                    Text(
                        text = "See All",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier
                            .clickable { onAddTxClick() }
                            .padding(4.dp)
                    )
                }
            }
        }

        // Display up to 4 transactions on dashboard with staggered animation
        val dashboardTx = transactions.take(4)
        if (dashboardTx.isEmpty()) {
            item {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(24.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(text = "No recorded transactions. Create your first!", color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f), fontSize = 13.sp)
                }
            }
        } else {
            itemsIndexed(
                items = dashboardTx,
                key = { _: Int, tx: TransactionEntity -> tx.id }
            ) { index: Int, tx: TransactionEntity ->
                AnimatedVisibility(
                    visible = true,
                    enter = AnimationUtils.staggeredEnter(index = index)
                ) {
                    TransactionRow(tx = tx)
                }
            }
        }
    }
}

@Composable
fun SummaryCard(
    title: String,
    value: String,
    icon: ImageVector,
    color: Color,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(20.dp),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.1f)),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Box(
                    modifier = Modifier
                        .size(36.dp)
                        .clip(CircleShape)
                        .background(color.copy(alpha = 0.15f)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = icon,
                        contentDescription = title,
                        tint = color,
                        modifier = Modifier.size(18.dp)
                    )
                }
                Text(
                    text = title,
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    fontWeight = FontWeight.Medium
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = value,
                fontSize = 22.sp,
                fontWeight = FontWeight.Black,
                color = MaterialTheme.colorScheme.onSurface
            )
        }
    }
}

private fun getGreeting(): String {
    val calendar = Calendar.getInstance()
    val hour = calendar.get(Calendar.HOUR_OF_DAY)
    return when (hour) {
        in 0..11 -> "Morning"
        in 12..16 -> "Afternoon"
        else -> "Evening"
    }
}

// ==================== TRANSACTIONS VIEW ====================

@Composable
fun TransactionsScreenView(
    transactions: List<TransactionEntity>,
    onDeleteTransaction: (Int, Double, String, String) -> Unit
) {
    var searchQuery by remember { mutableStateOf("") }
    var selectedFilter by remember { mutableStateOf("ALL") } // ALL, INCOME, EXPENSE

    val filteredTransactions = transactions.filter {
        val matchesSearch = it.title.contains(searchQuery, ignoreCase = true) ||
                it.category.contains(searchQuery, ignoreCase = true) ||
                it.tags.contains(searchQuery, ignoreCase = true)
        val matchesFilter = selectedFilter == "ALL" || it.type == selectedFilter
        matchesSearch && matchesFilter
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Search Bar
        OutlinedTextField(
            value = searchQuery,
            onValueChange = { searchQuery = it },
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 12.dp)
                .testTag("search_bar"),
            placeholder = { Text("Search transactions, tags, notes...", color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f)) },
            leadingIcon = { Icon(Icons.Default.Search, contentDescription = "Search", tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f)) },
            shape = RoundedCornerShape(24.dp),
            colors = OutlinedTextFieldDefaults.colors(
                focusedTextColor = MaterialTheme.colorScheme.onSurface,
                unfocusedTextColor = MaterialTheme.colorScheme.onSurface,
                focusedBorderColor = MaterialTheme.colorScheme.primary,
                unfocusedBorderColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.3f),
                focusedContainerColor = MaterialTheme.colorScheme.surface,
                unfocusedContainerColor = MaterialTheme.colorScheme.surface
            )
        )

        // Segmented Tabs Filter
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 16.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            listOf("ALL" to "All", "INCOME" to "Income", "EXPENSE" to "Expenses").forEach { (filterVal, label) ->
                val isSelected = selectedFilter == filterVal
                Button(
                    onClick = { selectedFilter = filterVal },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (isSelected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surface,
                        contentColor = if (isSelected) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant
                    ),
                    shape = RoundedCornerShape(20.dp),
                    border = BorderStroke(1.dp, if (isSelected) Color.Transparent else MaterialTheme.colorScheme.outline.copy(alpha = 0.15f)),
                    modifier = Modifier
                        .weight(1f)
                        .height(38.dp)
                        .testTag("filter_btn_$filterVal")
                ) {
                    Text(text = label, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
            }
        }

        // Ledger List
        if (filteredTransactions.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(
                        imageVector = Icons.Default.Inbox,
                        contentDescription = "Empty",
                        tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.4f),
                        modifier = Modifier.size(48.dp)
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(text = "No matching items found.", color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f), fontSize = 14.sp)
                }
            }
        } else {
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.weight(1f)
            ) {
                items(filteredTransactions) { tx ->
                    SwipeToDeleteContainer(
                        onDelete = {
                            onDeleteTransaction(tx.id, tx.amount, tx.category, tx.type)
                        }
                    ) {
                        TransactionRow(tx = tx)
                    }
                }
            }
        }
    }
}

@Composable
fun TransactionRow(tx: TransactionEntity) {
    val isExpense = tx.type == "EXPENSE"
    val isTransfer = tx.type == "TRANSFER"

    val icon = when (tx.category.lowercase()) {
        "food" -> Icons.Default.Restaurant
        "salary" -> Icons.Default.Payments
        "rent" -> Icons.Default.Home
        "shopping" -> Icons.Default.ShoppingBag
        "utilities" -> Icons.Default.ElectricalServices
        "investments" -> Icons.Default.TrendingUp
        else -> Icons.Default.AttachMoney
    }

    val iconColor = if (isExpense) BentoError else if (isTransfer) BentoPrimary else BentoAccentGreen

    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        shape = RoundedCornerShape(20.dp),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.08f)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(CircleShape)
                    .background(iconColor.copy(alpha = 0.12f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(imageVector = icon, contentDescription = tx.category, tint = iconColor)
            }
            Spacer(modifier = Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = tx.title,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onSurface,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Text(text = tx.category, fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f))
                    if (tx.tags.isNotEmpty()) {
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(6.dp))
                                .background(MaterialTheme.colorScheme.primaryContainer)
                                .padding(horizontal = 6.dp, vertical = 2.dp)
                        ) {
                            Text(text = tx.tags, fontSize = 9.sp, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    text = if (isExpense) "-$${String.format(Locale.US, "%.2f", tx.amount)}" else if (isTransfer) "$${String.format(Locale.US, "%.2f", tx.amount)}" else "+$${String.format(Locale.US, "%.2f", tx.amount)}",
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Black,
                    color = iconColor
                )
                Text(
                    text = SimpleDateFormat("MMM d, HH:mm", Locale.getDefault()).format(Date(tx.timestamp)),
                    fontSize = 10.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
                )
            }
        }
    }
}

// ==================== BUDGETS SCREEN ====================

@Composable
fun BudgetsScreenView(
    budgets: List<BudgetEntity>,
    goals: List<GoalEntity>,
    onAddBudget: () -> Unit,
    onAddGoal: () -> Unit,
    onDeleteBudget: (Int) -> Unit,
    onDeleteGoal: (Int) -> Unit,
    onContributeGoal: (Int, Double) -> Unit
) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Section: Budgets
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(text = "Category Limits", fontSize = 18.sp, fontWeight = FontWeight.Black, color = MaterialTheme.colorScheme.onBackground)
                Text(
                    text = "+ Create",
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.clickable { onAddBudget() }
                )
            }
        }

        if (budgets.isEmpty()) {
            item {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(24.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(text = "No active monthly budgets configured.", color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f), fontSize = 13.sp)
                }
            }
        } else {
            items(budgets) { budget ->
                val progress = if (budget.limitAmount > 0) (budget.spentAmount / budget.limitAmount).toFloat() else 0f
                val isOverspent = budget.spentAmount > budget.limitAmount
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    shape = RoundedCornerShape(20.dp),
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.08f)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(text = budget.category, fontSize = 15.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                            IconButton(onClick = { onDeleteBudget(budget.id) }) {
                                Icon(Icons.Default.Delete, contentDescription = "Delete", tint = BentoError.copy(alpha = 0.6f), modifier = Modifier.size(18.dp))
                            }
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        LinearProgressIndicator(
                            progress = { progress.coerceIn(0f, 1f) },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(8.dp)
                                .clip(RoundedCornerShape(4.dp)),
                            color = if (isOverspent) BentoError else BentoAccentGreen,
                            trackColor = MaterialTheme.colorScheme.surfaceVariant
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(text = "$${String.format(Locale.US, "%,.0f", budget.spentAmount)} spent", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text(text = "$${String.format(Locale.US, "%,.0f", budget.limitAmount)} limit", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }
            }
        }

        // Section: Goals
        item {
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(text = "Savings Goals", fontSize = 18.sp, fontWeight = FontWeight.Black, color = MaterialTheme.colorScheme.onBackground)
                Text(
                    text = "+ Create",
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.clickable { onAddGoal() }
                )
            }
        }

        if (goals.isEmpty()) {
            item {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(24.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(text = "No savings goals set. Start saving today!", color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f), fontSize = 13.sp)
                }
            }
        } else {
            items(goals) { goal ->
                val progress = if (goal.targetAmount > 0) (goal.currentAmount / goal.targetAmount).toFloat() else 0f
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    shape = RoundedCornerShape(20.dp),
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.08f)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(text = goal.name, fontSize = 15.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                                Text(text = "$${String.format(Locale.US, "%,.0f", goal.currentAmount)} / $${String.format(Locale.US, "%,.0f", goal.targetAmount)}", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                var showContribute by remember { mutableStateOf(false) }
                                IconButton(onClick = { showContribute = true }) {
                                    Icon(Icons.Default.Add, contentDescription = "Contribute", tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(20.dp))
                                }
                                IconButton(onClick = { onDeleteGoal(goal.id) }) {
                                    Icon(Icons.Default.Delete, contentDescription = "Delete", tint = BentoError.copy(alpha = 0.6f), modifier = Modifier.size(18.dp))
                                }
                                if (showContribute) {
                                    var amount by remember { mutableStateOf("") }
                                    AlertDialog(
                                        onDismissRequest = { showContribute = false },
                                        title = { Text("Contribute to ${goal.name}") },
                                        text = {
                                            OutlinedTextField(
                                                value = amount,
                                                onValueChange = { amount = it },
                                                label = { Text("Amount") },
                                                singleLine = true
                                            )
                                        },
                                        confirmButton = {
                                            Button(onClick = {
                                                amount.toDoubleOrNull()?.let { amt ->
                                                    onContributeGoal(goal.id, amt)
                                                }
                                                showContribute = false
                                            }) { Text("Add") }
                                        },
                                        dismissButton = {
                                            TextButton(onClick = { showContribute = false }) { Text("Cancel") }
                                        }
                                    )
                                }
                            }
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        LinearProgressIndicator(
                            progress = { progress.coerceIn(0f, 1f) },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(8.dp)
                                .clip(RoundedCornerShape(4.dp)),
                            color = BentoPrimary,
                            trackColor = MaterialTheme.colorScheme.surfaceVariant
                        )
                    }
                }
            }
        }
    }
}

// ==================== BILLS SCREEN ====================

@Composable
fun BillsScreenView(
    bills: List<BillEntity>,
    debts: List<DebtEntity>,
    onPayBill: (Int) -> Unit,
    onDeleteBill: (Int) -> Unit,
    onPayDebt: (Int, Double) -> Unit,
    onAddDebtClick: () -> Unit,
    onDeleteDebt: (Int) -> Unit
) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Section: Bills
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(text = "Upcoming Bills", fontSize = 18.sp, fontWeight = FontWeight.Black, color = MaterialTheme.colorScheme.onBackground)
            }
        }

        if (bills.isEmpty()) {
            item {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(24.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(text = "No bills recorded.", color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f), fontSize = 13.sp)
                }
            }
        } else {
            items(bills) { bill ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    shape = RoundedCornerShape(20.dp),
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.08f)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            modifier = Modifier
                                .size(44.dp)
                                .clip(RoundedCornerShape(12.dp))
                                .background(if (bill.isPaid) BentoAccentGreen.copy(alpha = 0.15f) else BentoError.copy(alpha = 0.15f)),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                imageVector = if (bill.isPaid) Icons.Default.CheckCircle else Icons.Default.Pending,
                                contentDescription = if (bill.isPaid) "Paid" else "Pending",
                                tint = if (bill.isPaid) BentoAccentGreen else BentoError
                            )
                        }
                        Spacer(modifier = Modifier.width(12.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(text = bill.name, fontSize = 14.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                            Text(text = "$${String.format(Locale.US, "%,.0f", bill.amount)} • ${bill.category}", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        if (!bill.isPaid) {
                            TextButton(onClick = { onPayBill(bill.id) }) {
                                Text("Pay", color = BentoAccentGreen, fontWeight = FontWeight.Bold)
                            }
                        }
                        IconButton(onClick = { onDeleteBill(bill.id) }) {
                            Icon(Icons.Default.Delete, contentDescription = "Delete", tint = BentoError.copy(alpha = 0.6f), modifier = Modifier.size(18.dp))
                        }
                    }
                }
            }
        }

        // Section: Debts
        item {
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(text = "Debts", fontSize = 18.sp, fontWeight = FontWeight.Black, color = MaterialTheme.colorScheme.onBackground)
                Text(
                    text = "+ Add",
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.clickable { onAddDebtClick() }
                )
            }
        }

        if (debts.isEmpty()) {
            item {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(24.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(text = "No debts recorded.", color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f), fontSize = 13.sp)
                }
            }
        } else {
            items(debts) { debt ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    shape = RoundedCornerShape(20.dp),
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.08f)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(text = debt.name, fontSize = 14.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                                Text(text = "${debt.type} • ${debt.interestRate}% APR", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                            IconButton(onClick = { onDeleteDebt(debt.id) }) {
                                Icon(Icons.Default.Delete, contentDescription = "Delete", tint = BentoError.copy(alpha = 0.6f), modifier = Modifier.size(18.dp))
                            }
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(text = "Balance: $${String.format(Locale.US, "%,.0f", debt.totalBalance)}", fontSize = 13.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                            Text(text = "Min: $${String.format(Locale.US, "%,.0f", debt.repaymentAmount)}/mo", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }
            }
        }
    }
}

// ==================== ASSISTANT SCREEN ====================

@Composable
fun AssistantScreenView(viewModel: FinanceViewModel) {
    val chatHistory by viewModel.chatHistory.collectAsStateWithLifecycle()
    val isAiThinking by viewModel.isAiThinking.collectAsStateWithLifecycle()
    var inputMessage by remember { mutableStateOf("") }
    val listState = androidx.compose.foundation.lazy.rememberLazyListState()

    // Auto-scroll to bottom when new messages arrive
    LaunchedEffect(chatHistory.size) {
        if (chatHistory.isNotEmpty()) {
            listState.animateScrollToItem(chatHistory.size - 1)
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Text(
            text = "AI Financial Advisor",
            fontSize = 18.sp,
            fontWeight = FontWeight.Black,
            color = MaterialTheme.colorScheme.onBackground,
            modifier = Modifier.padding(bottom = 12.dp)
        )

        LazyColumn(
            state = listState,
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(chatHistory) { message ->
                val isUser = message.role == "user"
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 4.dp),
                    horizontalAlignment = if (isUser) Alignment.End else Alignment.Start
                ) {
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = if (isUser) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant
                        ),
                        shape = RoundedCornerShape(
                            topStart = 16.dp,
                            topEnd = 16.dp,
                            bottomStart = if (isUser) 16.dp else 4.dp,
                            bottomEnd = if (isUser) 4.dp else 16.dp
                        )
                    ) {
                        Text(
                            text = message.text,
                            modifier = Modifier.padding(12.dp),
                            fontSize = 13.sp,
                            color = if (isUser) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
            if (isAiThinking) {
                item {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                        shape = RoundedCornerShape(4.dp, 16.dp, 16.dp, 16.dp)
                    ) {
                        Row(
                            modifier = Modifier.padding(12.dp),
                            horizontalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            repeat(3) {
                                Box(
                                    modifier = Modifier
                                        .size(8.dp)
                                        .clip(CircleShape)
                                        .background(MaterialTheme.colorScheme.primary.copy(alpha = 0.5f))
                                )
                            }
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Input Row
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            OutlinedTextField(
                value = inputMessage,
                onValueChange = { inputMessage = it },
                modifier = Modifier
                    .weight(1f)
                    .testTag("chat_input"),
                placeholder = { Text("Ask about your finances...") },
                shape = RoundedCornerShape(24.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedContainerColor = MaterialTheme.colorScheme.surface,
                    unfocusedContainerColor = MaterialTheme.colorScheme.surface
                ),
                singleLine = true
            )
            FilledIconButton(
                onClick = {
                    if (inputMessage.isNotBlank()) {
                        viewModel.sendChatMessage(inputMessage)
                        inputMessage = ""
                    }
                },
                modifier = Modifier.size(48.dp),
                shape = CircleShape
            ) {
                Icon(Icons.Default.Send, contentDescription = "Send")
            }
        }
    }
}

// ==================== DIALOGS ====================

@Composable
fun AddTransactionDialog(
    onDismiss: () -> Unit,
    onConfirm: (String, Double, String, String, String, String) -> Unit
) {
    var title by remember { mutableStateOf("") }
    var amount by remember { mutableStateOf("") }
    var category by remember { mutableStateOf("") }
    var type by remember { mutableStateOf("EXPENSE") }
    var note by remember { mutableStateOf("") }
    var tags by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Transaction", fontWeight = FontWeight.Bold) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(value = title, onValueChange = { title = it }, label = { Text("Title") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = amount, onValueChange = { amount = it }, label = { Text("Amount") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = category, onValueChange = { category = it }, label = { Text("Category") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilterChip(selected = type == "EXPENSE", onClick = { type = "EXPENSE" }, label = { Text("Expense") })
                    FilterChip(selected = type == "INCOME", onClick = { type = "INCOME" }, label = { Text("Income") })
                }
                OutlinedTextField(value = note, onValueChange = { note = it }, label = { Text("Note (optional)") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = tags, onValueChange = { tags = it }, label = { Text("Tags (optional)") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            }
        },
        confirmButton = {
            Button(onClick = {
                val amt = amount.toDoubleOrNull() ?: 0.0
                if (title.isNotBlank() && amt > 0 && category.isNotBlank()) {
                    onConfirm(title, amt, category, type, note, tags)
                }
            }) { Text("Add") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}

@Composable
fun AddBudgetDialog(
    onDismiss: () -> Unit,
    onConfirm: (String, Double) -> Unit
) {
    var category by remember { mutableStateOf("") }
    var limit by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("New Budget", fontWeight = FontWeight.Bold) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(value = category, onValueChange = { category = it }, label = { Text("Category") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = limit, onValueChange = { limit = it }, label = { Text("Monthly Limit") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            }
        },
        confirmButton = {
            Button(onClick = {
                val lim = limit.toDoubleOrNull() ?: 0.0
                if (category.isNotBlank() && lim > 0) onConfirm(category, lim)
            }) { Text("Create") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}

@Composable
fun AddGoalDialog(
    onDismiss: () -> Unit,
    onConfirm: (String, Double, Double) -> Unit
) {
    var name by remember { mutableStateOf("") }
    var target by remember { mutableStateOf("") }
    var current by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("New Goal", fontWeight = FontWeight.Bold) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(value = name, onValueChange = { name = it }, label = { Text("Goal Name") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = target, onValueChange = { target = it }, label = { Text("Target Amount") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = current, onValueChange = { current = it }, label = { Text("Current Amount") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            }
        },
        confirmButton = {
            Button(onClick = {
                val t = target.toDoubleOrNull() ?: 0.0
                val c = current.toDoubleOrNull() ?: 0.0
                if (name.isNotBlank() && t > 0) onConfirm(name, t, c)
            }) { Text("Create") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}

@Composable
fun AddDebtDialog(
    onDismiss: () -> Unit,
    onConfirm: (String, String, Double, Double, Double) -> Unit
) {
    var name by remember { mutableStateOf("") }
    var type by remember { mutableStateOf("LOAN") }
    var total by remember { mutableStateOf("") }
    var interest by remember { mutableStateOf("") }
    var payment by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Debt", fontWeight = FontWeight.Bold) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(value = name, onValueChange = { name = it }, label = { Text("Debt Name") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilterChip(selected = type == "LOAN", onClick = { type = "LOAN" }, label = { Text("Loan") })
                    FilterChip(selected = type == "CREDIT_CARD", onClick = { type = "CREDIT_CARD" }, label = { Text("Credit Card") })
                }
                OutlinedTextField(value = total, onValueChange = { total = it }, label = { Text("Total Balance") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = interest, onValueChange = { interest = it }, label = { Text("Interest Rate %") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = payment, onValueChange = { payment = it }, label = { Text("Min Payment") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            }
        },
        confirmButton = {
            Button(onClick = {
                val t = total.toDoubleOrNull() ?: 0.0
                val i = interest.toDoubleOrNull() ?: 0.0
                val p = payment.toDoubleOrNull() ?: 0.0
                if (name.isNotBlank() && t > 0) onConfirm(name, type, t, i, p)
            }) { Text("Add") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}

@Composable
fun AddBillDialog(
    onDismiss: () -> Unit,
    onConfirm: (String, Double, String) -> Unit
) {
    var name by remember { mutableStateOf("") }
    var amount by remember { mutableStateOf("") }
    var category by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("New Bill", fontWeight = FontWeight.Bold) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(value = name, onValueChange = { name = it }, label = { Text("Bill Name") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = amount, onValueChange = { amount = it }, label = { Text("Amount") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = category, onValueChange = { category = it }, label = { Text("Category") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            }
        },
        confirmButton = {
            Button(onClick = {
                val amt = amount.toDoubleOrNull() ?: 0.0
                if (name.isNotBlank() && amt > 0 && category.isNotBlank()) onConfirm(name, amt, category)
            }) { Text("Add") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}

// ==================== SWIPE TO DELETE ====================

@Composable
fun SwipeToDeleteContainer(
    onDelete: () -> Unit,
    content: @Composable () -> Unit
) {
    var offsetX by remember { mutableFloatStateOf(0f) }
    val threshold = -200f

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(20.dp))
    ) {
        // Delete background
        Box(
            modifier = Modifier
                .matchParentSize()
                .background(BentoError)
                .padding(end = 20.dp),
            contentAlignment = Alignment.CenterEnd
        ) {
            Icon(
                imageVector = Icons.Default.Delete,
                contentDescription = "Delete",
                tint = Color.White
            )
        }

        // Content
        Box(
            modifier = Modifier
                .offset(x = offsetX.dp)
                .clickable(
                    interactionSource = remember { androidx.compose.foundation.interaction.MutableInteractionSource() },
                    indication = null
                ) { }
        ) {
            content()
        }
    }
}