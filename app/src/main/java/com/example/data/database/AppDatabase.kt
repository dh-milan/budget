package com.example.data.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
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

@Database(
    entities = [
        TransactionEntity::class,
        BudgetEntity::class,
        GoalEntity::class,
        DebtEntity::class,
        BillEntity::class
    ],
    version = 1,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun transactionDao(): TransactionDao
    abstract fun budgetDao(): BudgetDao
    abstract fun goalDao(): GoalDao
    abstract fun debtDao(): DebtDao
    abstract fun billDao(): BillDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "wealthflow_database"
                )
                .fallbackToDestructiveMigration()
                .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
