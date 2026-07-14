package com.example

import android.app.Application
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import com.example.data.api.RetrofitClient
import com.example.workers.SyncWorker
import java.util.concurrent.TimeUnit

class WealthFlowApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        // CRITICAL: Initialize encrypted prefs FIRST before any token operations
        RetrofitClient.initialize(this)
        setupSyncWorker()
    }

    private fun setupSyncWorker() {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED) // Only run when network is available
            .build()

        val syncWorkRequest = PeriodicWorkRequestBuilder<SyncWorker>(15, TimeUnit.MINUTES)
            .setConstraints(constraints)
            .build()

        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            SyncWorker.WORK_NAME,
            ExistingPeriodicWorkPolicy.KEEP, // Keep existing work if already scheduled
            syncWorkRequest
        )
    }
}
