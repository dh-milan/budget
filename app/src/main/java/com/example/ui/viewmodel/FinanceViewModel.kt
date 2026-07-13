package com.example.ui.viewmodel

import android.app.Application
import android.content.Context
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.data.database.AppDatabase
import com.example.data.repository.FinanceRepository
import com.example.data.model.*
import com.example.data.api.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import com.example.BuildConfig
import android.util.Log
import android.widget.Toast

class FinanceViewModel(application: Application) : AndroidViewModel(application) {
    private val database = AppDatabase.getDatabase(application)
    private val repository = FinanceRepository(
        database.transactionDao(),
        database.budgetDao(),
        database.goalDao(),
        database.debtDao(),
        database.billDao()
    )
    
    // Backend API client
    private val apiService = RetrofitClient.apiService
    private val context = application.applicationContext
    
    private var authToken: String? = null

    // Reactive flows
    val transactions: StateFlow<List<TransactionEntity>> = repository.allTransactions
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val budgets: StateFlow<List<BudgetEntity>> = repository.allBudgets
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val goals: StateFlow<List<GoalEntity>> = repository.allGoals
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val debts: StateFlow<List<DebtEntity>> = repository.allDebts
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val bills: StateFlow<List<BillEntity>> = repository.allBills
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    // Chat states
    private val _chatHistory = MutableStateFlow<List<ChatMessage>>(
        listOf(ChatMessage("model", "Hello! I am your WealthFlow AI Financial Assistant. Ask me anything about your budgets, transactions, savings opportunities, or general finance!"))
    )
    val chatHistory: StateFlow<List<ChatMessage>> = _chatHistory.asStateFlow()

    private val _isAiThinking = MutableStateFlow(false)
    val isAiThinking: StateFlow<Boolean> = _isAiThinking.asStateFlow()

    // Database Actions
    fun addTransaction(title: String, amount: Double, category: String, type: String, note: String, tags: String, isRecurring: Boolean = false) {
        viewModelScope.launch {
            val trans = TransactionEntity(
                title = title,
                amount = amount,
                category = category,
                type = type,
                timestamp = System.currentTimeMillis(),
                note = note,
                tags = tags,
                isRecurring = isRecurring
            )
            repository.insertTransaction(trans)
            
            // Auto update spent amount on corresponding budget
            if (type == "EXPENSE") {
                val currentBudgets = budgets.value
                val existingBudget = currentBudgets.find { it.category.equals(category, ignoreCase = true) }
                if (existingBudget != null) {
                    repository.updateBudget(existingBudget.copy(spentAmount = existingBudget.spentAmount + amount))
                }
            }
        }
    }

    fun deleteTransaction(id: Int, amount: Double, category: String, type: String) {
        viewModelScope.launch {
            repository.deleteTransaction(id)
            if (type == "EXPENSE") {
                val currentBudgets = budgets.value
                val existingBudget = currentBudgets.find { it.category.equals(category, ignoreCase = true) }
                if (existingBudget != null) {
                    val newSpent = (existingBudget.spentAmount - amount).coerceAtLeast(0.0)
                    repository.updateBudget(existingBudget.copy(spentAmount = newSpent))
                }
            }
        }
    }

    fun addBudget(category: String, limit: Double) {
        viewModelScope.launch {
            // Calculate existing spent for this category
            val spent = transactions.value
                .filter { it.type == "EXPENSE" && it.category.equals(category, ignoreCase = true) }
                .sumOf { it.amount }
            repository.insertBudget(BudgetEntity(category = category, limitAmount = limit, spentAmount = spent))
        }
    }

    fun deleteBudget(id: Int) {
        viewModelScope.launch { repository.deleteBudget(id) }
    }

    fun addGoal(name: String, target: Double, current: Double, targetDate: Long) {
        viewModelScope.launch {
            repository.insertGoal(GoalEntity(name = name, targetAmount = target, currentAmount = current, targetDate = targetDate))
        }
    }

    fun contributeToGoal(id: Int, contribution: Double) {
        viewModelScope.launch {
            val goal = goals.value.find { it.id == id }
            if (goal != null) {
                repository.updateGoal(goal.copy(currentAmount = goal.currentAmount + contribution))
            }
        }
    }

    fun deleteGoal(id: Int) {
        viewModelScope.launch { repository.deleteGoal(id) }
    }

    fun addDebt(name: String, type: String, total: Double, interest: Double, dueDate: Long, payment: Double) {
        viewModelScope.launch {
            repository.insertDebt(DebtEntity(name = name, type = type, totalBalance = total, interestRate = interest, dueDate = dueDate, repaymentAmount = payment))
        }
    }

    fun payDebt(id: Int, payment: Double) {
        viewModelScope.launch {
            val debt = debts.value.find { it.id == id }
            if (debt != null) {
                val newBalance = (debt.totalBalance - payment).coerceAtLeast(0.0)
                repository.updateDebt(debt.copy(totalBalance = newBalance))
            }
        }
    }

    fun deleteDebt(id: Int) {
        viewModelScope.launch { repository.deleteDebt(id) }
    }

    fun addBill(name: String, amount: Double, dueDate: Long, category: String) {
        viewModelScope.launch {
            repository.insertBill(BillEntity(name = name, amount = amount, dueDate = dueDate, category = category))
        }
    }

    fun markBillAsPaid(id: Int) {
        viewModelScope.launch {
            val bill = bills.value.find { it.id == id }
            if (bill != null) {
                repository.updateBill(bill.copy(isPaid = true))
                // Log as expense
                addTransaction(
                    title = "Bill: ${bill.name}",
                    amount = bill.amount,
                    category = bill.category,
                    type = "EXPENSE",
                    note = "Automatically paid bill",
                    tags = "Bill, Paid"
                )
            }
        }
    }

    fun deleteBill(id: Int) {
        viewModelScope.launch { repository.deleteBill(id) }
    }

    // AI Agent Integration
    fun sendChatMessage(message: String) {
        if (message.isBlank()) return
        val userMessage = ChatMessage("user", message)
        _chatHistory.update { it + userMessage }

        _isAiThinking.value = true
        viewModelScope.launch {
            try {
                // Let's gather financial context to inject as a system prompt so the AI knows real financial state!
                val txCount = transactions.value.size
                val totalIncome = transactions.value.filter { it.type == "INCOME" }.sumOf { it.amount }
                val totalExpense = transactions.value.filter { it.type == "EXPENSE" }.sumOf { it.amount }
                val activeBudgets = budgets.value.joinToString { "${it.category}: Limit $${it.limitAmount}, Spent $${it.spentAmount}" }
                val activeGoals = goals.value.joinToString { "${it.name}: Progress $${it.currentAmount} / $${it.targetAmount}" }
                val activeDebts = debts.value.joinToString { "${it.name} (${it.type}): Balance $${it.totalBalance}, Interest ${it.interestRate}%" }
                val upcomingBills = bills.value.filter { !it.isPaid }.joinToString { "${it.name}: $${it.amount} due soon" }

                val systemPrompt = """
                    You are WealthFlow's elite AI Financial Assistant. You have access to the user's real-time local financial profile:
                    - Total Income: $${totalIncome}
                    - Total Expenses: $${totalExpense}
                    - Cash Flow: $${totalIncome - totalExpense}
                    - Transactions Count: ${txCount}
                    - Active Budgets: [${activeBudgets}]
                    - Savings Goals: [${activeGoals}]
                    - Debts: [${activeDebts}]
                    - Upcoming Unpaid Bills: [${upcomingBills}]

                    Provide highly professional, accurate, actionable, and secure financial advice. Answer questions briefly. Format numeric values beautifully as currency. Speak with professional composure. Keep responses under 200 words.
                """.trimIndent()

                // Compile history
                val apiKey = BuildConfig.GEMINI_API_KEY
                if (apiKey.isEmpty() || apiKey == "MY_GEMINI_API_KEY") {
                    // Provide intelligent local fallback response without API
                    val localResponse = generateLocalFinancialAdvice(message, totalIncome, totalExpense, budgets, goals, debts, bills)
                    _chatHistory.update { it + ChatMessage("model", localResponse) }
                    _isAiThinking.value = false
                    return@launch
                }

                // Call Gemini Direct REST
                val request = GeminiRequest(
                    contents = listOf(
                        GeminiContent(parts = listOf(GeminiPart(text = "$systemPrompt\n\nUser Question: $message")))
                    )
                )
                val response = GeminiClient.apiService.generateContent(apiKey, request)
                val reply = response.candidates.firstOrNull()?.content?.parts?.firstOrNull()?.text
                    ?: "I'm sorry, I couldn't formulate financial advice at this moment. Let's look at your local charts instead."

                _chatHistory.update { it + ChatMessage("model", reply) }
            } catch (e: Exception) {
                Log.e("FinanceViewModel", "Gemini error", e)
                // Provide local fallback on error
                val localResponse = generateLocalFinancialAdvice(message, totalIncome, totalExpense, budgets, goals, debts, bills)
                _chatHistory.update { it + ChatMessage("model", localResponse) }
            } finally {
                _isAiThinking.value = false
            }
        }
    }

    // Export CSV Helper
    fun exportToCsv(): String {
        val sb = StringBuilder()
        sb.append("ID,Title,Amount,Category,Type,Timestamp,Note,Tags,Recurring\n")
        transactions.value.forEach {
            sb.append("${it.id},\"${it.title.replace("\"", "\"\"")}\",${it.amount},\"${it.category}\",\"${it.type}\",${it.timestamp},\"${it.note.replace("\"", "\"\"")}\",\"${it.tags}\",${it.isRecurring}\n")
        }
        return sb.toString()
    }

    // No mock data - app starts fresh and connects to backend
    fun prepopulateData() {
        // Data will be loaded from backend API when connected
        loadDataFromBackend()
    }
    
    // Backend API Integration
    private fun loadDataFromBackend() {
        viewModelScope.launch {
            try {
                val token = authToken
                if (token != null) {
                    // Load transactions from backend
                    val remoteTransactions = apiService.getTransactions("Bearer $token")
                    remoteTransactions.forEach { netTx ->
                        val trans = TransactionEntity(
                            id = netTx.id.toIntOrNull() ?: 0,
                            title = netTx.title,
                            amount = netTx.amount.toDoubleOrNull() ?: 0.0,
                            category = netTx.category,
                            type = netTx.type,
                            timestamp = System.currentTimeMillis(),
                            note = netTx.note,
                            tags = "",
                            isRecurring = netTx.is_recurring
                        )
                        repository.insertTransaction(trans)
                    }
                }
            } catch (e: Exception) {
                Log.e("FinanceViewModel", "Backend sync error", e)
                // App continues with local data if backend is not available
            }
        }
    }
    
    fun login(email: String, password: String) {
        viewModelScope.launch {
            try {
                val response = apiService.login(LoginRequest(email, password))
                authToken = response.access
                Toast.makeText(context, "Login successful!", Toast.LENGTH_SHORT).show()
                loadDataFromBackend()
            } catch (e: Exception) {
                Log.e("FinanceViewModel", "Login error", e)
                Toast.makeText(context, "Login failed: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    // Local financial advice generator (works without API)
    private fun generateLocalFinancialAdvice(
        message: String,
        totalIncome: Double,
        totalExpense: Double,
        budgets: List<BudgetEntity>,
        goals: List<GoalEntity>,
        debts: List<DebtEntity>,
        bills: List<BillEntity>
    ): String {
        val cashFlow = totalIncome - totalExpense
        val lowerMessage = message.lowercase()

        return when {
            lowerMessage.contains("budget") || lowerMessage.contains("suggest") -> {
                if (budgets.isEmpty()) {
                    "You haven't set up any budgets yet. Start by creating category limits for Food, Shopping, Rent, and Utilities to track your spending effectively."
                } else {
                    val overspent = budgets.filter { it.spentAmount > it.limitAmount }
                    if (overspent.isNotEmpty()) {
                        "Alert: You're over budget in ${overspent.joinToString { it.category }}. Consider reducing spending in these categories or increasing your limits."
                    } else {
                        "You're managing your budgets well. Consider allocating 20% of your income to savings goals for better financial health."
                    }
                }
            }
            lowerMessage.contains("save") || lowerMessage.contains("goal") -> {
                if (goals.isEmpty()) {
                    "You haven't set any savings goals. Start by creating an emergency fund goal - aim for 3-6 months of expenses."
                } else {
                    val activeGoals = goals.joinToString { "${it.name}: $${String.format("%,.0f", it.currentAmount)} / $${String.format("%,.0f", it.targetAmount)}" }
                    "Your active goals: $activeGoals. Keep contributing consistently to reach your targets faster."
                }
            }
            lowerMessage.contains("debt") || lowerMessage.contains("loan") -> {
                if (debts.isEmpty()) {
                    "You have no recorded debts. Great financial discipline! Consider investing your surplus cash flow."
                } else {
                    val highInterest = debts.filter { it.interestRate > 10 }
                    if (highInterest.isNotEmpty()) {
                        "Priority: Pay off high-interest debts first: ${highInterest.joinToString { "${it.name} (${it.interestRate}%)" }}. This will save you money on interest payments."
                    } else {
                        "You have ${debts.size} active debt(s). Continue making regular payments to reduce your total balance."
                    }
                }
            }
            lowerMessage.contains("spend") || lowerMessage.contains("expense") -> {
                if (totalExpense > totalIncome) {
                    "Warning: Your expenses ($${String.format("%,.2f", totalExpense)}) exceed your income ($${String.format("%,.2f", totalIncome)}). Review your spending patterns and cut non-essential expenses."
                } else {
                    "Your spending is within healthy limits. You have a positive cash flow of $${String.format("%,.2f", cashFlow)}. Consider investing the surplus."
                }
            }
            lowerMessage.contains("bill") -> {
                val unpaidBills = bills.filter { !it.isPaid }
                if (unpaidBills.isEmpty()) {
                    "All bills are paid! You're in great shape. Set up automatic payments to maintain this streak."
                } else {
                    "You have ${unpaidBills.size} unpaid bill(s) totaling $${String.format("%,.2f", unpaidBills.sumOf { it.amount })}. Prioritize these payments to avoid late fees."
                }
            }
            else -> {
                when {
                    cashFlow > 0 -> "Your financial health looks good with a positive cash flow of $${String.format("%,.2f", cashFlow)}. Focus on building emergency savings and investing for long-term growth."
                    cashFlow < 0 -> "Your expenses exceed income by $${String.format("%,.2f", kotlin.math.abs(cashFlow))}. Review your budget and identify areas to reduce spending."
                    else -> "Your income and expenses are balanced. This is a good time to set up savings goals and investment plans for the future."
                }
            }
        }
    }
}

data class ChatMessage(val role: String, val text: String)
