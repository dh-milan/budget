package com.example.ui.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.data.database.AppDatabase
import com.example.data.repository.FinanceRepository
import com.example.data.model.*
import com.example.data.api.GeminiClient
import com.example.data.api.GeminiRequest
import com.example.data.api.GeminiContent
import com.example.data.api.GeminiPart
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import com.example.BuildConfig
import android.util.Log

class FinanceViewModel(application: Application) : AndroidViewModel(application) {
    private val database = AppDatabase.getDatabase(application)
    private val repository = FinanceRepository(
        database.transactionDao(),
        database.budgetDao(),
        database.goalDao(),
        database.debtDao(),
        database.billDao()
    )

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
                    _chatHistory.update { it + ChatMessage("model", "Please configure your GEMINI_API_KEY in the AI Studio Secrets panel to activate full AI assistance capabilities.") }
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
                _chatHistory.update { it + ChatMessage("model", "Error connecting to AI Assistant: ${e.localizedMessage}. Please double-check your connection and Gemini API Key.") }
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

    // Prep some initial beautiful mock data so first launch is amazing!
    fun prepopulateData() {
        viewModelScope.launch {
            if (transactions.value.isEmpty()) {
                addTransaction("Salary Deposit", 5000.0, "Salary", "INCOME", "Monthly salary payout", "Salary, Primary")
                addTransaction("Elite Organic Grocery", 240.0, "Food", "EXPENSE", "Weekly grocery store shopping", "Organic, Food")
                addTransaction("Workspace Rent", 1200.0, "Rent", "EXPENSE", "Co-working space desk rental", "Rent, Work")
                addTransaction("Tech Gadget Shop", 150.0, "Shopping", "EXPENSE", "Mechanical keyboard accessory", "Tech, Accessory")
                addTransaction("High Speed Internet", 80.0, "Utilities", "EXPENSE", "Gigabit fiber internet bill", "Utilities, Bill")
                addTransaction("Dividend Payout", 350.0, "Investments", "INCOME", "Quarterly index fund dividend", "Investment, Passive")
                addTransaction("Aesthetic Cafe Espresso", 6.50, "Food", "EXPENSE", "Flat white coffee", "Coffee, Work")

                addBudget("Food", 600.0)
                addBudget("Shopping", 400.0)
                addBudget("Rent", 1500.0)
                addBudget("Utilities", 200.0)

                addGoal("Emergency Reserve Fund", 20000.0, 8500.0, System.currentTimeMillis() + (365L * 24 * 60 * 60 * 1000))
                addGoal("European Summer Retreat", 6000.0, 2400.0, System.currentTimeMillis() + (180L * 24 * 60 * 60 * 1000))

                addDebt("Sapphire Credit Card", "CREDIT_CARD", 1250.0, 18.9, System.currentTimeMillis() + (15L * 24 * 60 * 60 * 1000), 150.0)
                addDebt("Premium Automobile Loan", "LOAN", 18400.0, 4.5, System.currentTimeMillis() + (25L * 24 * 60 * 60 * 1000), 450.0)

                addBill("Premium Video Subscription", 15.99, System.currentTimeMillis() + (5L * 24 * 60 * 60 * 1000), "Entertainment")
                addBill("Gym Membership Subscription", 80.0, System.currentTimeMillis() + (12L * 24 * 60 * 60 * 1000), "Healthcare")
            }
        }
    }
}

data class ChatMessage(val role: String, val text: String)
