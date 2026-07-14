package com.example.notifications

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import android.util.Log
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

class WealthFlowMessagingService : FirebaseMessagingService() {

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        Log.d("FCM", "New Token: $token")
        // Send token to backend for push notification registration
        sendTokenToBackend(token)
    }

    private fun sendTokenToBackend(token: String) {
        // This will be called when the FCM token is refreshed
        // The token should be sent to the backend API endpoint:
        // POST /api/v1/auth/register-device/
        // Body: { "fcm_token": token, "device_type": "android" }
        Log.d("FCM", "Token ready for backend registration: $token")
    }

    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)
        
        // Handle smart triggers (e.g. Budget Warnings, Bill Reminders) sent from backend
        val title = message.notification?.title ?: message.data["title"] ?: "WealthFlow Alert"
        val body = message.notification?.body ?: message.data["body"] ?: "You have a new message"
        
        showNotification(title, body)
    }

    private fun showNotification(title: String, body: String) {
        val channelId = "wealthflow_alerts"
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "Smart Alerts",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Budget warnings and bill reminders"
            }
            notificationManager.createNotificationChannel(channel)
        }

        val builder = NotificationCompat.Builder(this, channelId)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(body)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)

        notificationManager.notify(System.currentTimeMillis().toInt(), builder.build())
    }
}
