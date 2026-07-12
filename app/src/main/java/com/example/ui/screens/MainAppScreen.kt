package com.example.ui.screens

import android.widget.Toast
import androidx.compose.animation.*
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.automirrored.outlined.Chat
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
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
import com.example.ui.viewmodel.FinanceViewModel
import java.text.SimpleDateFormat
import java.util.*

sealed class ScreenTab(val title: String, val icon: ImageVector) {
    object Dashboard : ScreenTab("Insights", Icons.Default.Dashboard)
    object Transactions : ScreenTab("Ledger", Icons.Default.ReceiptLong)
    object Budgets : ScreenTab("Budgets", Icons.Default.PieChart)
    object Bills : ScreenTab("Bills & Debt", Icons.Default.CreditCard)
    object Assistant : ScreenTab("AI Advisor", Icons.AutoMirrored.Outlined.Chat)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainAppScreen(viewModel: FinanceViewModel) {
    val context = LocalContext.current
    val clipboardManager = LocalClipboardManager.current

    // Trigger initial prepopulated data
    LaunchedEffect(Unit) {
        viewModel.prepopulateData()
    }

    // States
    var currentTab by remember { mutableStateOf<ScreenTab>(ScreenTab.Dashboard) }
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

    Scaffold(
        modifier = Modifier.fillMaxSize(),
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
                            text = "WEALTHFLOW",
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
                    ScreenTab.Assistant
                )
                tabs.forEach { tab ->
                    NavigationBarItem(
                        selected = currentTab == tab,
                        onClick = { currentTab = tab },
                        icon = { Icon(tab.icon, contentDescription = tab.title) },
                        label = { Text(tab.title, fontSize = 11.sp) },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = MaterialTheme.colorScheme.primary,
                            selectedTextColor = MaterialTheme.colorScheme.primary,
                            indicatorColor = MaterialTheme.colorScheme.primaryContainer,
                            unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f),
                            unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f)
                        ),
                        modifier = Modifier.testTag("nav_tab_${tab.title.lowercase()}")
                    )
                }
            }
        },
        floatingActionButton = {
            if (currentTab != ScreenTab.Assistant) {
                ExtendedFloatingActionButton(
                    onClick = {
                        when (currentTab) {
                            ScreenTab.Dashboard -> showAddTxDialog = true
                            ScreenTab.Transactions -> showAddTxDialog = true
                            ScreenTab.Budgets -> showAddBudgetDialog = true
                            ScreenTab.Bills -> showAddBillDialog = true
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
                                ScreenTab.Assistant -> "Ask AI"
                            }
                        )
                    },
                    modifier = Modifier.testTag("fab_add_action")
                )
            }
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            Crossfade(targetState = currentTab, label = "TabTransition") { tab ->
                when (tab) {
                    ScreenTab.Dashboard -> DashboardScreenView(
                        transactions = transactions,
                        budgets = budgets,
                        goals = goals,
                        onAddTxClick = { showAddTxDialog = true },
                        onAddGoalClick = { showAddGoalDialog = true }
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
                    ScreenTab.Assistant -> AssistantScreenView(viewModel)
                }
            }
        }
    }

    // Dialogs
    if (showAddTxDialog) {
        AddTransactionDialog(
            onDismiss = { showAddTxDialog = false },
            onConfirm = { title, amount, category, type, note, tags ->
                viewModel.addTransaction(title, amount, category, type, note, tags)
                showAddTxDialog = false
            }
        )
    }

    if (showAddBudgetDialog) {
        AddBudgetDialog(
            onDismiss = { showAddBudgetDialog = false },
            onConfirm = { category, limit ->
                viewModel.addBudget(category, limit)
                showAddBudgetDialog = false
            }
        )
    }

    if (showAddGoalDialog) {
        AddGoalDialog(
            onDismiss = { showAddGoalDialog = false },
            onConfirm = { name, target, current ->
                viewModel.addGoal(name, target, current, System.currentTimeMillis() + (30L * 24 * 60 * 60 * 1000))
                showAddGoalDialog = false
            }
        )
    }

    if (showAddDebtDialog) {
        AddDebtDialog(
            onDismiss = { showAddDebtDialog = false },
            onConfirm = { name, type, total, interest, payment ->
                viewModel.addDebt(name, type, total, interest, System.currentTimeMillis() + (30L * 24 * 60 * 60 * 1000), payment)
                showAddDebtDialog = false
            }
        )
    }

    if (showAddBillDialog) {
        AddBillDialog(
            onDismiss = { showAddBillDialog = false },
            onConfirm = { name, amount, category ->
                viewModel.addBill(name, amount, System.currentTimeMillis() + (15L * 24 * 60 * 60 * 1000), category)
                showAddBillDialog = false
            }
        )
    }
}

// ==================== DASHBOARD VIEW ====================

@Composable
fun DashboardScreenView(
    transactions: List<TransactionEntity>,
    budgets: List<BudgetEntity>,
    goals: List<GoalEntity>,
    onAddTxClick: () -> Unit,
    onAddGoalClick: () -> Unit
) {
    val totalIncome = transactions.filter { it.type == "INCOME" }.sumOf { it.amount }
    val totalExpense = transactions.filter { it.type == "EXPENSE" }.sumOf { it.amount }
    val netWorth = totalIncome - totalExpense

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Premium Greeting Header Item (Bento Style)
        item {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "Good Morning,",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                    )
                    Text(
                        text = "Alex Rivera",
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
                        text = "AR",
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                }
            }
        }

        // Hero Card (Double-column width representation in grid style)
        item {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(180.dp)
                    .clip(RoundedCornerShape(28.dp))
            ) {
                Image(
                    painter = painterResource(id = R.drawable.img_hero_dashboard),
                    contentDescription = "Futuristic Chart Layout",
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop
                )
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(
                            Brush.verticalGradient(
                                listOf(
                                    Color.Transparent,
                                    Color.Black.copy(alpha = 0.7f)
                                )
                            )
                        )
                )
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
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(12.dp))
                                .background(Color.White.copy(alpha = 0.2f))
                                .padding(horizontal = 8.dp, vertical = 4.dp)
                        ) {
                            Text(
                                text = "+2.4%",
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                        }
                    }
                    Column {
                        Text(
                            text = "$${String.format("%,.2f", netWorth)}",
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
                                Text(text = " +$${String.format("%,.0f", totalIncome)}", fontSize = 11.sp, color = Color(0xFF81C784))
                            }
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.ArrowDownward, contentDescription = "Expense", tint = Color(0xFFE57373), modifier = Modifier.size(12.dp))
                                Text(text = " -$${String.format("%,.0f", totalExpense)}", fontSize = 11.sp, color = Color(0xFFE57373))
                            }
                        }
                    }
                }
            }
        }

        // Actionable Micro-Insights Panel (Bento style AI Advice block)
        item {
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
                            text = "AI FINANCIAL INSIGHT",
                            fontSize = 10.sp,
                            fontWeight = FontWeight.ExtraBold,
                            color = MaterialTheme.colorScheme.primary,
                            letterSpacing = 1.2.sp
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = if (netWorth > 0) {
                                "Your Cash Flow is highly healthy today! We recommend putting $500 into your European Retreat goal to reach your target 2 weeks early."
                            } else {
                                "Warning: Expenses exceed deposits this period. Ask your AI Advisor for instant cost-reduction opportunities."
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

        // Custom Interactive Analytics Custom Chart Drawing (Bento styled grid)
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                shape = RoundedCornerShape(24.dp),
                border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.12f)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Cash Flow Analytics",
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    Text(
                        text = "Interactive breakdown of recent transactions and trends",
                        fontSize = 11.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
                        modifier = Modifier.padding(bottom = 16.dp)
                    )

                    // Draw custom graph
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(130.dp)
                    ) {
                        Canvas(modifier = Modifier.fillMaxSize()) {
                            val linePath = Path()
                            val width = size.width
                            val height = size.height

                            // Draw reference grid lines
                            val gridColor = BentoOutline.copy(alpha = 0.15f)
                            for (i in 1..3) {
                                drawLine(
                                    color = gridColor,
                                    start = Offset(0f, height * i / 4),
                                    end = Offset(width, height * i / 4),
                                    strokeWidth = 2f
                                )
                            }

                            // Dynamic Line generation representing expenditures trend
                            val points = listOf(
                                Offset(0f, height * 0.8f),
                                Offset(width * 0.2f, height * 0.6f),
                                Offset(width * 0.4f, height * 0.75f),
                                Offset(width * 0.6f, height * 0.4f),
                                Offset(width * 0.8f, height * 0.5f),
                                Offset(width, height * 0.2f)
                            )

                            linePath.moveTo(points[0].x, points[0].y)
                            for (i in 1 until points.size) {
                                linePath.quadraticTo(
                                    (points[i - 1].x + points[i].x) / 2,
                                    (points[i - 1].y + points[i].y) / 2,
                                    points[i].x,
                                    points[i].y
                                )
                            }

                            // Fill area under line with soft metallic gradient
                            val fillPath = Path().apply {
                                addPath(linePath)
                                lineTo(width, height)
                                lineTo(0f, height)
                                close()
                            }

                            drawPath(
                                path = fillPath,
                                brush = Brush.verticalGradient(
                                    listOf(BentoPrimary.copy(alpha = 0.2f), Color.Transparent)
                                )
                            )

                            drawPath(
                                path = linePath,
                                color = BentoPrimary,
                                style = Stroke(width = 6f)
                            )

                            // Highlight current point
                            drawCircle(
                                color = BentoPrimary,
                                radius = 8f,
                                center = Offset(width, height * 0.2f)
                            )
                        }
                    }

                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 8.dp),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(text = "WK 1", fontSize = 9.sp, color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f))
                        Text(text = "WK 2", fontSize = 9.sp, color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f))
                        Text(text = "WK 3", fontSize = 9.sp, color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f))
                        Text(text = "WK 4", fontSize = 9.sp, color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f))
                        Text(text = "NOW", fontSize = 9.sp, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        // Recent Activity Header Title
        item {
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

        // Display up to 4 transactions on dashboard
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
            items(dashboardTx) { tx ->
                TransactionRow(tx = tx, onDelete = {})
            }
        }
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
                        TransactionRow(tx = tx, onDelete = {
                            onDeleteTransaction(tx.id, tx.amount, tx.category, tx.type)
                        })
                    }
                }
            }
        }
    }
}

@Composable
fun TransactionRow(tx: TransactionEntity, onDelete: () -> Unit) {
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
                    text = if (isExpense) "-$${String.format("%.2f", tx.amount)}" else if (isTransfer) "$${String.format("%.2f", tx.amount)}" else "+$${String.format("%.2f", tx.amount)}",
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
                val progressColor = if (isOverspent) BentoError else if (progress > 0.8f) BentoAccentGold else BentoAccentGreen

                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    shape = RoundedCornerShape(24.dp),
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.1f))
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Column {
                                Text(text = budget.category, fontSize = 15.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                                Text(
                                    text = "Spent $${String.format("%.2f", budget.spentAmount)} of $${budget.limitAmount}",
                                    fontSize = 11.sp,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                                )
                            }
                            IconButton(onClick = { onDeleteBudget(budget.id) }) {
                                Icon(Icons.Default.Delete, contentDescription = "Delete", tint = BentoError.copy(alpha = 0.7f))
                            }
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        LinearProgressIndicator(
                            progress = { progress.coerceAtMost(1f) },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(8.dp)
                                .clip(CircleShape),
                            color = progressColor,
                            trackColor = MaterialTheme.colorScheme.surfaceVariant
                        )
                    }
                }
            }
        }

        // Section: Goals
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(text = "Savings Goals", fontSize = 18.sp, fontWeight = FontWeight.Black, color = MaterialTheme.colorScheme.onBackground)
                Text(
                    text = "+ New Goal",
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
                    Text(text = "No active savings targets set.", color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f), fontSize = 13.sp)
                }
            }
        } else {
            items(goals) { goal ->
                val progress = if (goal.targetAmount > 0) (goal.currentAmount / goal.targetAmount).toFloat() else 0f
                var contributionAmount by remember { mutableStateOf("") }

                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    shape = RoundedCornerShape(24.dp),
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.1f))
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Column {
                                Text(text = goal.name, fontSize = 15.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                                Text(
                                    text = "$${String.format("%,.0f", goal.currentAmount)} of $${String.format("%,.0f", goal.targetAmount)} accrued",
                                    fontSize = 11.sp,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                                )
                            }
                            IconButton(onClick = { onDeleteGoal(goal.id) }) {
                                Icon(Icons.Default.Delete, contentDescription = "Delete", tint = BentoError.copy(alpha = 0.7f))
                            }
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        LinearProgressIndicator(
                            progress = { progress.coerceAtMost(1f) },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(8.dp)
                                .clip(CircleShape),
                            color = MaterialTheme.colorScheme.primary,
                            trackColor = MaterialTheme.colorScheme.surfaceVariant
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            OutlinedTextField(
                                value = contributionAmount,
                                onValueChange = { contributionAmount = it },
                                modifier = Modifier
                                    .weight(1f)
                                    .height(50.dp),
                                placeholder = { Text("Amount", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f)) },
                                shape = RoundedCornerShape(12.dp),
                                colors = OutlinedTextFieldDefaults.colors(
                                    focusedTextColor = MaterialTheme.colorScheme.onSurface,
                                    unfocusedTextColor = MaterialTheme.colorScheme.onSurface,
                                    focusedBorderColor = MaterialTheme.colorScheme.primary,
                                    unfocusedBorderColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.15f)
                                )
                            )
                            Button(
                                onClick = {
                                    val amt = contributionAmount.toDoubleOrNull() ?: 0.0
                                    if (amt > 0) {
                                        onContributeGoal(goal.id, amt)
                                        contributionAmount = ""
                                    }
                                },
                                shape = RoundedCornerShape(12.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                            ) {
                                Text("Invest", fontSize = 11.sp)
                            }
                        }
                    }
                }
            }
        }
    }
}

// ==================== BILLS & DEBTS VIEW ====================

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
            Text(text = "Upcoming Bills Calendar", fontSize = 18.sp, fontWeight = FontWeight.Black, color = MaterialTheme.colorScheme.onBackground)
        }

        val unpaidBills = bills.filter { !it.isPaid }
        if (unpaidBills.isEmpty()) {
            item {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(text = "Hooray! All bills are settled for this period.", color = BentoAccentGreen, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                }
            }
        } else {
            items(unpaidBills) { bill ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    shape = RoundedCornerShape(24.dp),
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.1f))
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
                                .background(BentoAccentGold.copy(alpha = 0.12f)),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(Icons.Default.CalendarToday, contentDescription = "Due", tint = BentoAccentGold)
                        }
                        Spacer(modifier = Modifier.width(12.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(text = bill.name, fontSize = 14.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                            Text(
                                text = "Due " + SimpleDateFormat("MMM d, yyyy", Locale.getDefault()).format(Date(bill.dueDate)),
                                fontSize = 11.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                            )
                        }
                        Text(
                            text = "$${String.format("%.2f", bill.amount)}",
                            fontSize = 15.sp,
                            fontWeight = FontWeight.Black,
                            color = MaterialTheme.colorScheme.onSurface,
                            modifier = Modifier.padding(horizontal = 8.dp)
                        )
                        Row(
                            horizontalArrangement = Arrangement.spacedBy(4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Button(
                                onClick = { onPayBill(bill.id) },
                                colors = ButtonDefaults.buttonColors(containerColor = BentoAccentGreen),
                                contentPadding = PaddingValues(horizontal = 12.dp),
                                shape = RoundedCornerShape(10.dp)
                            ) {
                                Text("Pay", fontSize = 10.sp, color = Color.White, fontWeight = FontWeight.Bold)
                            }
                            IconButton(onClick = { onDeleteBill(bill.id) }) {
                                Icon(Icons.Default.Delete, contentDescription = "Delete", tint = BentoError.copy(alpha = 0.7f))
                            }
                        }
                    }
                }
            }
        }

        // Section: Debts
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(text = "Liability Manager", fontSize = 18.sp, fontWeight = FontWeight.Black, color = MaterialTheme.colorScheme.onBackground)
                Text(
                    text = "+ Add Debt",
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
                    Text(text = "No recorded credit cards or loans.", color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f), fontSize = 13.sp)
                }
            }
        } else {
            items(debts) { debt ->
                var payAmount by remember { mutableStateOf("") }

                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    shape = RoundedCornerShape(24.dp),
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.1f))
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Column {
                                Text(
                                    text = debt.name,
                                    fontSize = 15.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                                Text(
                                    text = "Interest: ${debt.interestRate}% | Min Due: $${debt.repaymentAmount}",
                                    fontSize = 11.sp,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                                )
                            }
                            IconButton(onClick = { onDeleteDebt(debt.id) }) {
                                Icon(Icons.Default.Delete, contentDescription = "Delete", tint = BentoError.copy(alpha = 0.7f))
                            }
                        }
                        Spacer(modifier = Modifier.height(12.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.Bottom
                        ) {
                            Column {
                                Text(text = "TOTAL BALANCE", fontSize = 9.sp, color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f), letterSpacing = 1.sp)
                                Text(
                                    text = "$${String.format("%,.2f", debt.totalBalance)}",
                                    fontSize = 24.sp,
                                    fontWeight = FontWeight.Black,
                                    color = BentoError
                                )
                            }
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                OutlinedTextField(
                                    value = payAmount,
                                    onValueChange = { payAmount = it },
                                    modifier = Modifier
                                        .width(90.dp)
                                        .height(50.dp),
                                    placeholder = { Text("Pay", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f)) },
                                    shape = RoundedCornerShape(12.dp),
                                    colors = OutlinedTextFieldDefaults.colors(
                                        focusedTextColor = MaterialTheme.colorScheme.onSurface,
                                        unfocusedTextColor = MaterialTheme.colorScheme.onSurface,
                                        focusedBorderColor = MaterialTheme.colorScheme.primary,
                                        unfocusedBorderColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.15f)
                                    )
                                )
                                Button(
                                    onClick = {
                                        val amt = payAmount.toDoubleOrNull() ?: 0.0
                                        if (amt > 0) {
                                            onPayDebt(debt.id, amt)
                                            payAmount = ""
                                        }
                                    },
                                    shape = RoundedCornerShape(12.dp),
                                    colors = ButtonDefaults.buttonColors(containerColor = BentoError)
                                ) {
                                    Text("Settle", fontSize = 11.sp)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

// ==================== AI ASSISTANT VIEW ====================

@Composable
fun AssistantScreenView(viewModel: FinanceViewModel) {
    val chatHistory by viewModel.chatHistory.collectAsStateWithLifecycle()
    val isThinking by viewModel.isAiThinking.collectAsStateWithLifecycle()
    var inputQuery by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Chat History terminal
        LazyColumn(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .padding(bottom = 12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            reverseLayout = false
        ) {
            items(chatHistory) { msg ->
                val isAi = msg.role == "model"
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = if (isAi) Arrangement.Start else Arrangement.End
                ) {
                    Box(
                        modifier = Modifier
                            .clip(
                                RoundedCornerShape(
                                    topStart = 16.dp,
                                    topEnd = 16.dp,
                                    bottomStart = if (isAi) 0.dp else 16.dp,
                                    bottomEnd = if (isAi) 16.dp else 0.dp
                                )
                            )
                            .background(if (isAi) MaterialTheme.colorScheme.surface else MaterialTheme.colorScheme.primary)
                            .padding(12.dp)
                            .widthIn(max = 280.dp)
                    ) {
                        Text(
                            text = msg.text,
                            color = if (isAi) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onPrimary,
                            fontSize = 13.sp,
                            lineHeight = 18.sp
                        )
                    }
                }
            }

            if (isThinking) {
                item {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(8.dp),
                        horizontalArrangement = Arrangement.Start,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        CircularProgressIndicator(
                            color = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.size(16.dp),
                            strokeWidth = 2.dp
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "AI Advisor is analyzing portfolio...",
                            fontSize = 11.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }

        // Suggestion quick questions chips
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            val suggestions = listOf("Suggest a Budget", "Analyze Spend", "Savings Advice")
            suggestions.forEach { text ->
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(12.dp))
                        .background(MaterialTheme.colorScheme.surfaceVariant)
                        .clickable { viewModel.sendChatMessage(text) }
                        .padding(horizontal = 10.dp, vertical = 6.dp)
                ) {
                    Text(text = text, fontSize = 10.sp, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                }
            }
        }

        // Input row
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            OutlinedTextField(
                value = inputQuery,
                onValueChange = { inputQuery = it },
                modifier = Modifier
                    .weight(1f)
                    .testTag("chat_input"),
                placeholder = { Text("Ask about cash flows, goals...", color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f), fontSize = 13.sp) },
                shape = RoundedCornerShape(24.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = MaterialTheme.colorScheme.onSurface,
                    unfocusedTextColor = MaterialTheme.colorScheme.onSurface,
                    focusedBorderColor = MaterialTheme.colorScheme.primary,
                    unfocusedBorderColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.15f),
                    focusedContainerColor = MaterialTheme.colorScheme.surface,
                    unfocusedContainerColor = MaterialTheme.colorScheme.surface
                )
            )
            IconButton(
                onClick = {
                    if (inputQuery.isNotBlank()) {
                        viewModel.sendChatMessage(inputQuery)
                        inputQuery = ""
                    }
                },
                modifier = Modifier
                    .size(48.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.primary)
                    .testTag("send_chat_button")
            ) {
                Icon(
                    imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                    contentDescription = "Send",
                    tint = MaterialTheme.colorScheme.onPrimary
                )
            }
        }
    }
}

// ==================== SHARED FORMS & UTILS ====================

@Composable
fun AddTransactionDialog(onDismiss: () -> Unit, onConfirm: (String, Double, String, String, String, String) -> Unit) {
    var title by remember { mutableStateOf("") }
    var amount by remember { mutableStateOf("") }
    var category by remember { mutableStateOf("Food") }
    var type by remember { mutableStateOf("EXPENSE") } // INCOME, EXPENSE, TRANSFER
    var note by remember { mutableStateOf("") }
    var tags by remember { mutableStateOf("") }

    val categoriesList = listOf("Food", "Salary", "Rent", "Shopping", "Utilities", "Investments", "Entertainment", "Healthcare")

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Record New Ledger Entry", color = MaterialTheme.colorScheme.onSurface, fontWeight = FontWeight.Bold, fontSize = 16.sp) },
        containerColor = MaterialTheme.colorScheme.surface,
        confirmButton = {
            Button(
                onClick = {
                    val amt = amount.toDoubleOrNull() ?: 0.0
                    if (title.isNotBlank() && amt > 0.0) {
                        onConfirm(title, amt, category, type, note, tags)
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
                modifier = Modifier.testTag("confirm_tx_button")
            ) {
                Text("Post Entry")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel", color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                // Segmented Type
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                    listOf("EXPENSE" to "Expense", "INCOME" to "Income", "TRANSFER" to "Transfer").forEach { (valType, label) ->
                        val isSelected = type == valType
                        Button(
                            onClick = { type = valType },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = if (isSelected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant,
                                contentColor = if (isSelected) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant
                            ),
                            shape = RoundedCornerShape(12.dp),
                            modifier = Modifier
                                .weight(1f)
                                .height(38.dp)
                        ) {
                            Text(label, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                }

                OutlinedTextField(
                    value = title,
                    onValueChange = { title = it },
                    label = { Text("Title", color = MaterialTheme.colorScheme.onSurfaceVariant) },
                    modifier = Modifier
                        .fillMaxWidth()
                        .testTag("add_tx_title"),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = MaterialTheme.colorScheme.onSurface,
                        unfocusedTextColor = MaterialTheme.colorScheme.onSurface
                    )
                )

                OutlinedTextField(
                    value = amount,
                    onValueChange = { amount = it },
                    label = { Text("Amount ($)", color = MaterialTheme.colorScheme.onSurfaceVariant) },
                    modifier = Modifier
                        .fillMaxWidth()
                        .testTag("add_tx_amount"),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = MaterialTheme.colorScheme.onSurface,
                        unfocusedTextColor = MaterialTheme.colorScheme.onSurface
                    )
                )

                // Simple Category Spinner simulation
                Text("Category", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                LazyColumn(modifier = Modifier.height(60.dp).fillMaxWidth()) {
                    items(categoriesList) { cat ->
                        val isSelected = category == cat
                        Text(
                            text = cat,
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(if (isSelected) MaterialTheme.colorScheme.primaryContainer else Color.Transparent)
                                .clickable { category = cat }
                                .padding(8.dp),
                            color = if (isSelected) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onSurface,
                            fontSize = 12.sp
                        )
                    }
                }

                OutlinedTextField(
                    value = note,
                    onValueChange = { note = it },
                    label = { Text("Personal Memo", color = MaterialTheme.colorScheme.onSurfaceVariant) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = MaterialTheme.colorScheme.onSurface,
                        unfocusedTextColor = MaterialTheme.colorScheme.onSurface
                    )
                )

                OutlinedTextField(
                    value = tags,
                    onValueChange = { tags = it },
                    label = { Text("Filter tags (comma-separated)", color = MaterialTheme.colorScheme.onSurfaceVariant) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = MaterialTheme.colorScheme.onSurface,
                        unfocusedTextColor = MaterialTheme.colorScheme.onSurface
                    )
                )
            }
        }
    )
}

@Composable
fun AddBudgetDialog(onDismiss: () -> Unit, onConfirm: (String, Double) -> Unit) {
    var category by remember { mutableStateOf("Food") }
    var limit by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("New Monthly Budget Limit", color = MaterialTheme.colorScheme.onSurface, fontWeight = FontWeight.Bold) },
        containerColor = MaterialTheme.colorScheme.surface,
        confirmButton = {
            Button(
                onClick = {
                    val lim = limit.toDoubleOrNull() ?: 0.0
                    if (lim > 0) {
                        onConfirm(category, lim)
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
            ) {
                Text("Set Budget")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel", color = MaterialTheme.colorScheme.onSurfaceVariant) }
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = category,
                    onValueChange = { category = it },
                    label = { Text("Spending Category", color = MaterialTheme.colorScheme.onSurfaceVariant) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = MaterialTheme.colorScheme.onSurface,
                        unfocusedTextColor = MaterialTheme.colorScheme.onSurface
                    )
                )
                OutlinedTextField(
                    value = limit,
                    onValueChange = { limit = it },
                    label = { Text("Monthly Threshold Limit ($)", color = MaterialTheme.colorScheme.onSurfaceVariant) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = MaterialTheme.colorScheme.onSurface,
                        unfocusedTextColor = MaterialTheme.colorScheme.onSurface
                    )
                )
            }
        }
    )
}

@Composable
fun AddGoalDialog(onDismiss: () -> Unit, onConfirm: (String, Double, Double) -> Unit) {
    var name by remember { mutableStateOf("") }
    var target by remember { mutableStateOf("") }
    var current by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("New Financial Savings Target", color = MaterialTheme.colorScheme.onSurface, fontWeight = FontWeight.Bold) },
        containerColor = MaterialTheme.colorScheme.surface,
        confirmButton = {
            Button(
                onClick = {
                    val tgt = target.toDoubleOrNull() ?: 0.0
                    val cur = current.toDoubleOrNull() ?: 0.0
                    if (name.isNotBlank() && tgt > 0) {
                        onConfirm(name, tgt, cur)
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
            ) {
                Text("Deploy Goal")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel", color = MaterialTheme.colorScheme.onSurfaceVariant) }
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("Target Goal Name", color = MaterialTheme.colorScheme.onSurfaceVariant) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = MaterialTheme.colorScheme.onSurface,
                        unfocusedTextColor = MaterialTheme.colorScheme.onSurface
                    )
                )
                OutlinedTextField(
                    value = target,
                    onValueChange = { target = it },
                    label = { Text("Required Target Amount ($)", color = MaterialTheme.colorScheme.onSurfaceVariant) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = MaterialTheme.colorScheme.onSurface,
                        unfocusedTextColor = MaterialTheme.colorScheme.onSurface
                    )
                )
                OutlinedTextField(
                    value = current,
                    onValueChange = { current = it },
                    label = { Text("Initial Contribution Seed ($)", color = MaterialTheme.colorScheme.onSurfaceVariant) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = MaterialTheme.colorScheme.onSurface,
                        unfocusedTextColor = MaterialTheme.colorScheme.onSurface
                    )
                )
            }
        }
    )
}

@Composable
fun AddDebtDialog(onDismiss: () -> Unit, onConfirm: (String, String, Double, Double, Double) -> Unit) {
    var name by remember { mutableStateOf("") }
    var type by remember { mutableStateOf("CREDIT_CARD") }
    var total by remember { mutableStateOf("") }
    var interest by remember { mutableStateOf("") }
    var payment by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Register Liability Account", color = MaterialTheme.colorScheme.onSurface, fontWeight = FontWeight.Bold) },
        containerColor = MaterialTheme.colorScheme.surface,
        confirmButton = {
            Button(
                onClick = {
                    val tot = total.toDoubleOrNull() ?: 0.0
                    val intr = interest.toDoubleOrNull() ?: 0.0
                    val pay = payment.toDoubleOrNull() ?: 0.0
                    if (name.isNotBlank() && tot > 0) {
                        onConfirm(name, type, tot, intr, pay)
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
            ) {
                Text("Register Debt")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel", color = MaterialTheme.colorScheme.onSurfaceVariant) }
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("Lender / Credit Card Name", color = MaterialTheme.colorScheme.onSurfaceVariant) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = MaterialTheme.colorScheme.onSurface,
                        unfocusedTextColor = MaterialTheme.colorScheme.onSurface
                    )
                )
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf("CREDIT_CARD" to "Card", "LOAN" to "Loan").forEach { (vType, label) ->
                        val isSelected = type == vType
                        Button(
                            onClick = { type = vType },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = if (isSelected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant,
                                contentColor = if (isSelected) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant
                            ),
                            modifier = Modifier.weight(1f)
                        ) {
                            Text(label, fontSize = 11.sp)
                        }
                    }
                }
                OutlinedTextField(
                    value = total,
                    onValueChange = { total = it },
                    label = { Text("Current Balance ($)", color = MaterialTheme.colorScheme.onSurfaceVariant) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = MaterialTheme.colorScheme.onSurface,
                        unfocusedTextColor = MaterialTheme.colorScheme.onSurface
                    )
                )
                OutlinedTextField(
                    value = interest,
                    onValueChange = { interest = it },
                    label = { Text("APR Interest Rate (%)", color = MaterialTheme.colorScheme.onSurfaceVariant) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = MaterialTheme.colorScheme.onSurface,
                        unfocusedTextColor = MaterialTheme.colorScheme.onSurface
                    )
                )
                OutlinedTextField(
                    value = payment,
                    onValueChange = { payment = it },
                    label = { Text("Minimum Due Repayment ($)", color = MaterialTheme.colorScheme.onSurfaceVariant) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = MaterialTheme.colorScheme.onSurface,
                        unfocusedTextColor = MaterialTheme.colorScheme.onSurface
                    )
                )
            }
        }
    )
}

@Composable
fun AddBillDialog(onDismiss: () -> Unit, onConfirm: (String, Double, String) -> Unit) {
    var name by remember { mutableStateOf("") }
    var amount by remember { mutableStateOf("") }
    var category by remember { mutableStateOf("Utilities") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Register Upcoming Bill Profile", color = MaterialTheme.colorScheme.onSurface, fontWeight = FontWeight.Bold) },
        containerColor = MaterialTheme.colorScheme.surface,
        confirmButton = {
            Button(
                onClick = {
                    val amt = amount.toDoubleOrNull() ?: 0.0
                    if (name.isNotBlank() && amt > 0) {
                        onConfirm(name, amt, category)
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
            ) {
                Text("Schedule Bill")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel", color = MaterialTheme.colorScheme.onSurfaceVariant) }
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("Service Provider / Bill Name", color = MaterialTheme.colorScheme.onSurfaceVariant) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = MaterialTheme.colorScheme.onSurface,
                        unfocusedTextColor = MaterialTheme.colorScheme.onSurface
                    )
                )
                OutlinedTextField(
                    value = amount,
                    onValueChange = { amount = it },
                    label = { Text("Due Bill Amount ($)", color = MaterialTheme.colorScheme.onSurfaceVariant) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = MaterialTheme.colorScheme.onSurface,
                        unfocusedTextColor = MaterialTheme.colorScheme.onSurface
                    )
                )
                OutlinedTextField(
                    value = category,
                    onValueChange = { category = it },
                    label = { Text("Category (e.g. Utilities)", color = MaterialTheme.colorScheme.onSurfaceVariant) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = MaterialTheme.colorScheme.onSurface,
                        unfocusedTextColor = MaterialTheme.colorScheme.onSurface
                    )
                )
            }
        }
    )
}

@Composable
fun SwipeToDeleteContainer(onDelete: () -> Unit, content: @Composable () -> Unit) {
    Box(modifier = Modifier.fillMaxWidth()) {
        content()
    }
}

@Composable
fun Image(painter: androidx.compose.ui.graphics.painter.Painter, contentDescription: String, modifier: Modifier, contentScale: ContentScale) {
    androidx.compose.foundation.Image(
        painter = painter,
        contentDescription = contentDescription,
        modifier = modifier,
        contentScale = contentScale
    )
}
