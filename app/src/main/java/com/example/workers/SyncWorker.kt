package com.example.workers

import android.content.Context
import android.util.Log
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.example.data.database.AppDatabase
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class SyncWorker(
    appContext: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        val database = AppDatabase.getDatabase(applicationContext)
        val transactionDao = database.transactionDao()
        val budgetDao = database.budgetDao()
        val goalDao = database.goalDao()
        val debtDao = database.debtDao()
        val billDao = database.billDao()
        
        try {
            // 1. Fetch pending updates from local database (where syncStatus != SYNCED)
            val unsyncedTransactions = transactionDao.getUnsyncedTransactions()
            val unsyncedBudgets = budgetDao.getUnsyncedBudgets()
            val unsyncedGoals = goalDao.getUnsyncedGoals()
            val unsyncedDebts = debtDao.getUnsyncedDebts()
            val unsyncedBills = billDao.getUnsyncedBills()
            
            Log.d(WORK_NAME, "Syncing: ${unsyncedTransactions.size} transactions, ${unsyncedBudgets.size} budgets...")

            // 2. Simulate API Call: Push local changes to the backend API
            // val response = apiService.syncData(SyncRequest(unsyncedTransactions, ...))
            
            // 3. Mark items as SYNCED (Simulating a successful remote update)
            unsyncedTransactions.forEach { tx ->
                val mockRemoteId = tx.remoteId ?: "remote_tx_${tx.id}"
                transactionDao.markTransactionSynced(tx.id, mockRemoteId)
            }
            
            unsyncedBudgets.forEach { budget ->
                val mockRemoteId = budget.remoteId ?: "remote_bg_${budget.id}"
                budgetDao.markBudgetSynced(budget.id, mockRemoteId)
            }
            
            unsyncedGoals.forEach { goal ->
                val mockRemoteId = goal.remoteId ?: "remote_gl_${goal.id}"
                goalDao.markGoalSynced(goal.id, mockRemoteId)
            }
            
            unsyncedDebts.forEach { debt ->
                val mockRemoteId = debt.remoteId ?: "remote_dt_${debt.id}"
                debtDao.markDebtSynced(debt.id, mockRemoteId)
            }
            
            unsyncedBills.forEach { bill ->
                val mockRemoteId = bill.remoteId ?: "remote_bl_${bill.id}"
                billDao.markBillSynced(bill.id, mockRemoteId)
            }

            // 4. Fetch remote changes from backend (delta sync using last_sync timestamp)
            // val remoteChanges = apiService.getUpdates(lastSyncTimestamp)
            
            // 5. Update local database and resolve conflicts...

            Result.success()
        } catch (e: Exception) {
            Log.e(WORK_NAME, "Sync failed", e)
            Result.retry() // Instructs WorkManager to retry this work later
        }
    }
    
    companion object {
        const val WORK_NAME = "WealthFlowSyncWorker"
    }
}
