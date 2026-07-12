package com.example.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "transactions")
data class TransactionEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val title: String,
    val amount: Double,
    val category: String,
    val type: String, // "INCOME", "EXPENSE", "TRANSFER"
    val timestamp: Long,
    val note: String = "",
    val tags: String = "",
    val imagePath: String? = null,
    val isRecurring: Boolean = false
)

@Entity(tableName = "budgets")
data class BudgetEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val category: String,
    val limitAmount: Double,
    val spentAmount: Double = 0.0
)

@Entity(tableName = "goals")
data class GoalEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val name: String,
    val targetAmount: Double,
    val currentAmount: Double = 0.0,
    val targetDate: Long
)

@Entity(tableName = "debts")
data class DebtEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val name: String,
    val type: String, // "CREDIT_CARD", "LOAN"
    val totalBalance: Double,
    val interestRate: Double,
    val dueDate: Long,
    val repaymentAmount: Double
)

@Entity(tableName = "bills")
data class BillEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val name: String,
    val amount: Double,
    val dueDate: Long,
    val isPaid: Boolean = false,
    val category: String
)
