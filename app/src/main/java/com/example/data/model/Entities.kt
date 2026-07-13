package com.example.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

enum class SyncStatus {
    SYNCED,
    PENDING_INSERT,
    PENDING_UPDATE,
    PENDING_DELETE
}

@Entity(tableName = "transactions")
data class TransactionEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val remoteId: String? = null,
    val title: String,
    val amount: Double,
    val category: String,
    val type: String, // "INCOME", "EXPENSE", "TRANSFER"
    val timestamp: Long,
    val note: String = "",
    val tags: String = "",
    val imagePath: String? = null,
    val isRecurring: Boolean = false,
    val syncStatus: String = SyncStatus.PENDING_INSERT.name,
    val lastUpdated: Long = System.currentTimeMillis(),
    val isDeleted: Boolean = false
)

@Entity(tableName = "budgets")
data class BudgetEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val remoteId: String? = null,
    val category: String,
    val limitAmount: Double,
    val spentAmount: Double = 0.0,
    val syncStatus: String = SyncStatus.PENDING_INSERT.name,
    val lastUpdated: Long = System.currentTimeMillis(),
    val isDeleted: Boolean = false
)

@Entity(tableName = "goals")
data class GoalEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val remoteId: String? = null,
    val name: String,
    val targetAmount: Double,
    val currentAmount: Double = 0.0,
    val targetDate: Long,
    val syncStatus: String = SyncStatus.PENDING_INSERT.name,
    val lastUpdated: Long = System.currentTimeMillis(),
    val isDeleted: Boolean = false
)

@Entity(tableName = "debts")
data class DebtEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val remoteId: String? = null,
    val name: String,
    val type: String, // "CREDIT_CARD", "LOAN"
    val totalBalance: Double,
    val interestRate: Double,
    val dueDate: Long,
    val repaymentAmount: Double,
    val syncStatus: String = SyncStatus.PENDING_INSERT.name,
    val lastUpdated: Long = System.currentTimeMillis(),
    val isDeleted: Boolean = false
)

@Entity(tableName = "bills")
data class BillEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val remoteId: String? = null,
    val name: String,
    val amount: Double,
    val dueDate: Long,
    val isPaid: Boolean = false,
    val category: String,
    val syncStatus: String = SyncStatus.PENDING_INSERT.name,
    val lastUpdated: Long = System.currentTimeMillis(),
    val isDeleted: Boolean = false
)
