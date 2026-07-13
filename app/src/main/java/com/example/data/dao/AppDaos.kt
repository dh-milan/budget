package com.example.data.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.example.data.model.TransactionEntity
import com.example.data.model.BudgetEntity
import com.example.data.model.GoalEntity
import com.example.data.model.DebtEntity
import com.example.data.model.BillEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface TransactionDao {
    @Query("SELECT * FROM transactions ORDER BY timestamp DESC")
    fun getAllTransactions(): Flow<List<TransactionEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTransaction(transaction: TransactionEntity)

    @Query("DELETE FROM transactions WHERE id = :id")
    suspend fun deleteTransaction(id: Int)

    @Query("SELECT * FROM transactions WHERE syncStatus != 'SYNCED'")
    suspend fun getUnsyncedTransactions(): List<TransactionEntity>

    @Query("UPDATE transactions SET syncStatus = 'SYNCED', remoteId = :remoteId WHERE id = :localId")
    suspend fun markTransactionSynced(localId: Int, remoteId: String)
}

@Dao
interface BudgetDao {
    @Query("SELECT * FROM budgets")
    fun getAllBudgets(): Flow<List<BudgetEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBudget(budget: BudgetEntity)

    @Update
    suspend fun updateBudget(budget: BudgetEntity)

    @Query("DELETE FROM budgets WHERE id = :id")
    suspend fun deleteBudget(id: Int)

    @Query("SELECT * FROM budgets WHERE syncStatus != 'SYNCED'")
    suspend fun getUnsyncedBudgets(): List<BudgetEntity>

    @Query("UPDATE budgets SET syncStatus = 'SYNCED', remoteId = :remoteId WHERE id = :localId")
    suspend fun markBudgetSynced(localId: Int, remoteId: String)
}

@Dao
interface GoalDao {
    @Query("SELECT * FROM goals")
    fun getAllGoals(): Flow<List<GoalEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertGoal(goal: GoalEntity)

    @Update
    suspend fun updateGoal(goal: GoalEntity)

    @Query("DELETE FROM goals WHERE id = :id")
    suspend fun deleteGoal(id: Int)

    @Query("SELECT * FROM goals WHERE syncStatus != 'SYNCED'")
    suspend fun getUnsyncedGoals(): List<GoalEntity>

    @Query("UPDATE goals SET syncStatus = 'SYNCED', remoteId = :remoteId WHERE id = :localId")
    suspend fun markGoalSynced(localId: Int, remoteId: String)
}

@Dao
interface DebtDao {
    @Query("SELECT * FROM debts")
    fun getAllDebts(): Flow<List<DebtEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDebt(debt: DebtEntity)

    @Update
    suspend fun updateDebt(debt: DebtEntity)

    @Query("DELETE FROM debts WHERE id = :id")
    suspend fun deleteDebt(id: Int)

    @Query("SELECT * FROM debts WHERE syncStatus != 'SYNCED'")
    suspend fun getUnsyncedDebts(): List<DebtEntity>

    @Query("UPDATE debts SET syncStatus = 'SYNCED', remoteId = :remoteId WHERE id = :localId")
    suspend fun markDebtSynced(localId: Int, remoteId: String)
}

@Dao
interface BillDao {
    @Query("SELECT * FROM bills ORDER BY dueDate ASC")
    fun getAllBills(): Flow<List<BillEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBill(bill: BillEntity)

    @Update
    suspend fun updateBill(bill: BillEntity)

    @Query("DELETE FROM bills WHERE id = :id")
    suspend fun deleteBill(id: Int)

    @Query("SELECT * FROM bills WHERE syncStatus != 'SYNCED'")
    suspend fun getUnsyncedBills(): List<BillEntity>

    @Query("UPDATE bills SET syncStatus = 'SYNCED', remoteId = :remoteId WHERE id = :localId")
    suspend fun markBillSynced(localId: Int, remoteId: String)
}
