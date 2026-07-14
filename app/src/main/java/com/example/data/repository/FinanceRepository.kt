package com.example.data.repository

import com.example.data.dao.TransactionDao
import com.example.data.dao.BudgetDao
import com.example.data.dao.GoalDao
import com.example.data.dao.DebtDao
import com.example.data.dao.BillDao
import com.example.data.model.TransactionEntity
import com.example.data.model.BudgetEntity
import com.example.data.model.GoalEntity
import com.example.data.model.DebtEntity
import com.example.data.model.BillEntity
import kotlinx.coroutines.flow.Flow

class FinanceRepository(
    private val transactionDao: TransactionDao,
    private val budgetDao: BudgetDao,
    private val goalDao: GoalDao,
    private val debtDao: DebtDao,
    private val billDao: BillDao
) {
    val allTransactions: Flow<List<TransactionEntity>> = transactionDao.getAllTransactions()
    val allBudgets: Flow<List<BudgetEntity>> = budgetDao.getAllBudgets()
    val allGoals: Flow<List<GoalEntity>> = goalDao.getAllGoals()
    val allDebts: Flow<List<DebtEntity>> = debtDao.getAllDebts()
    val allBills: Flow<List<BillEntity>> = billDao.getAllBills()

    suspend fun insertTransaction(transaction: TransactionEntity) = transactionDao.insertTransaction(transaction)
    suspend fun deleteTransaction(id: Int) = transactionDao.deleteTransaction(id)

    suspend fun insertBudget(budget: BudgetEntity) = budgetDao.insertBudget(budget)
    suspend fun updateBudget(budget: BudgetEntity) = budgetDao.updateBudget(budget)
    suspend fun deleteBudget(id: Int) = budgetDao.deleteBudget(id)

    suspend fun insertGoal(goal: GoalEntity) = goalDao.insertGoal(goal)
    suspend fun updateGoal(goal: GoalEntity) = goalDao.updateGoal(goal)
    suspend fun deleteGoal(id: Int) = goalDao.deleteGoal(id)

    suspend fun insertDebt(debt: DebtEntity) = debtDao.insertDebt(debt)
    suspend fun updateDebt(debt: DebtEntity) = debtDao.updateDebt(debt)
    suspend fun deleteDebt(id: Int) = debtDao.deleteDebt(id)

    suspend fun insertBill(bill: BillEntity) = billDao.insertBill(bill)
    suspend fun updateBill(bill: BillEntity) = billDao.updateBill(bill)
    suspend fun deleteBill(id: Int) = billDao.deleteBill(id)

    suspend fun clearAll() {
        transactionDao.clearAll()
        budgetDao.clearAll()
        goalDao.clearAll()
        debtDao.clearAll()
        billDao.clearAll()
    }
}
