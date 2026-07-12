# 🌐 WealthFlow Phase 2: Complete System Architecture Blueprint

This document specifies the core engineering designs, data integration routes, message queue profiles, caching topologies, and security flows for the WealthFlow backend, client network adapters, and asynchronous task engine.

---

## 1. Secure OAuth2 & Google Identity Service Authentication Flow

To eliminate the operational risk of managing raw passwords, WealthFlow implements an OIDC/Google Sign-In flow with a secure cryptographic validation handshake on the backend.

### Detailed JWT Routing & Token Exchange Lifecycle

```
[ Client: Android App ]              [ Google Auth Identity ]           [ DRF Web API Service ]
          │                                     │                                  │
          │  1) Request Native Google Auth      │                                  │
          ├────────────────────────────────────►│                                  │
          │                                     │                                  │
          │  2) Authenticate & Return ID Token  │                                  │
          │◄────────────────────────────────────┤                                  │
          │                                                                        │
          │  3) Send ID Token to backend via API (POST /v1/auth/google/)           │
          ├───────────────────────────────────────────────────────────────────────►│
          │                                                                        │
          │                                             4) Verify Token against    │
          │                                                Google Token Endpoint   │
          │                                             ─────────────────────────┐ │
          │                                                                      │ │
          │                                             5) Find/Create DB record │ │
          │                                             6) Mint JWT Access/Refresh│◄
          │                                                                        │
          │  7) HTTP 200 OK (JWT Access & Refresh Token Body)                      │
          │◄───────────────────────────────────────────────────────────────────────┤
          │                                                                        │
          │  8) Encrypt Tokens in Keystore / EncryptedSharedPreferences            │
          ▼                                                                        ▼
```

### Backend Verification Mechanism (Python)

When the client passes the ID Token to `/v1/auth/google/`, the server executes this high-performance OIDC verification logic:

```python
# auth/views.py
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile

class GoogleAuthView(APIView):
    permission_classes = [] # Public login gateway

    def post(self, request):
        token = request.data.get("id_token")
        if not token:
            return Response({"error": "Google ID Token missing"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Cryptographically verify signature and validity directly using Google certificates
            id_info = id_token.verify_oauth2_token(
                token, 
                google_requests.Request(), 
                settings.GOOGLE_CLIENT_ID
            )

            # Ensure the audience matches the designated Android Client ID
            if id_info['aud'] != settings.GOOGLE_CLIENT_ID:
                raise ValueError('Invalid Client Identification Audience')

            # Identify target user using the unique 'sub' claim (never changes per account)
            sub_id = id_info['sub']
            email = id_info['email']
            name = id_info.get('name', '')
            avatar = id_info.get('picture', '')

            # Query database or provision record instantly (Stateless signup/signin)
            user, created = UserProfile.objects.get_or_create(
                google_subject_id=sub_id,
                defaults={
                    'email': email,
                    'full_name': name,
                    'avatar_url': avatar,
                    'role': 'USER'
                }
            )

            # Generate industry-standard stateless JWT Access & Refresh token pair
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.full_name,
                    "tier": user.subscription_tier
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"OIDC Authentication failed: {str(e)}"}, status=status.HTTP_401_UNAUTHORIZED)
```

---

## 2. Distributed Asynchronous Celery Workers & Task Engine

To maintain an agile, low-latency API response profile, heavy calculations are scheduled onto background worker nodes orchestrated via **Celery** with **Redis** as the message broker.

### Celery Background Job Configuration

```python
# core/celery.py
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wealthflow.settings')

app = Celery('wealthflow')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically scan all registered django apps for tasks.py modules
app.autodiscover_tasks()

# Configured Periodic Cron Tasks (Celery Beat Orchestration)
app.conf.beat_schedule = {
    'process-recurring-bills-every-midnight': {
        'task': 'bills.tasks.process_predicted_bills',
        'schedule': crontab(hour=0, minute=0),
    },
    'run-fraud-monitoring-audit-every-hour': {
        'task': 'security.tasks.audit_suspicious_activity',
        'schedule': crontab(minute=0),
    },
    'generate-ai-portfolio-health-scores-daily': {
        'task': 'ai.tasks.compute_health_scores',
        'schedule': crontab(hour=2, minute=0),
    }
}
```

### High-Priority Task Example: Transaction Auto-Categorization

When a user posts a transaction, the server triggers an asynchronous categorization job to avoid blocking the main thread:

```python
# ai/tasks.py
import stripe
from celery import shared_task
from .models import Transaction, Category
from .utils import call_gemini_categorizer

@shared_task(queue='ai_processing', max_retries=3, default_retry_delay=60)
def categorize_transaction_task(transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        
        # Request category tag predictions from the Gemini AI endpoint
        predicted_category = call_gemini_categorizer(
            title=transaction.title, 
            amount=transaction.amount,
            note=transaction.note
        )

        transaction.category = predicted_category
        transaction.save()

        # Update running category-limit stats inside Redis Cache instantly
        update_budget_redis_cache(transaction.account.user_id, predicted_category)

    except Transaction.DoesNotExist:
        # Avoid retrying if database transaction is missing
        pass
    except Exception as exc:
        raise categorize_transaction_task.retry(exc=exc)
```

---

## 3. Client Background Synchronization Strategy (Android WorkManager)

WealthFlow leverages an **Offline-First SQLite Cache Architecture**. All user modifications occur locally first via the **Room Database** and are continuously synchronized to the Django API in the background.

```kotlin
// sync/SyncWorker.kt
package com.example.sync

import android.content.Context
import androidx.work.*
import com.example.data.repository.FinanceRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject

class SyncWorker(
    context: Context,
    workerParams: WorkerParameters,
    private val repository: FinanceRepository
) : CoroutineWorker(context, workerParams) {

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        try {
            // Push locally created transactions that haven't been synchronized yet
            val dirtyTransactions = repository.getUnsyncedTransactions()
            dirtyTransactions.forEach { tx ->
                val success = repository.pushTransactionToServer(tx)
                if (success) {
                    repository.markTransactionSynced(tx.id)
                }
            }

            // Pull fresh ledger balances, budgets, and bills from the DRF backend
            repository.pullLedgerDataFromServer()

            Result.success()
        } catch (e: Exception) {
            if (runAttemptCount < 3) {
                Result.retry()
            } else {
                Result.failure()
            }
        }
    }
}
```

### Network constraints definition for Hilt injection configuration

We enforce network requirements to preserve user mobile data plans and protect battery levels:

```kotlin
// sync/SyncScheduler.kt
fun schedulePeriodSync(context: Context) {
    val constraints = Constraints.Builder()
        .setRequiredNetworkType(NetworkType.CONNECTED)
        .setRequiresBatteryNotLow(true)
        .build()

    val syncRequest = PeriodicWorkRequestBuilder<SyncWorker>(3, java.util.concurrent.TimeUnit.HOURS)
        .setConstraints(constraints)
        .setBackoffCriteria(
            BackoffPolicy.EXPONENTIAL,
            PeriodicWorkRequest.MIN_BACKOFF_MILLIS,
            java.util.concurrent.TimeUnit.MILLISECONDS
        )
        .build()

    WorkManager.getInstance(context).enqueueUniquePeriodicWork(
        "wealthflow_core_sync_engine",
        ExistingPeriodicWorkPolicy.KEEP,
        syncRequest
    )
}
```

---

## 4. Telemetry, Redis Caching Policies & Rate-Limiting

### Caching Strategy with Redis
- **Session Cache**: Store decoded JWT session strings with an explicit expiration TTL matching the access token (15 mins).
- **Read Cache**: Store common analytical endpoints (e.g. monthly category averages, running savings status). Evict cached values immediately when any write operations occur on the transactions entity.

```python
# utils/cache.py
import redis
import json

redis_client = redis.StrictRedis.from_url(settings.REDIS_URL, decode_responses=True)

def get_user_monthly_summary(user_id, month):
    cache_key = f"user_summary:{user_id}:{month}"
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        return json.loads(cached_data)
        
    # Cache Miss: Calculate statistics from PostgreSQL
    summary = compute_summary_from_db(user_id, month)
    redis_client.setex(cache_key, 3600, json.dumps(summary)) # TTL = 1 Hour
    return summary
```

### Production API Rate Limiting (DRF Settings)
To defend against automated denial-of-service queries and resource consumption attacks:

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLING_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/hour',
        'ai_copilot': '50/hour' # Protect expensive LLM APIs from brute force queries
    }
}
```

---

## 5. Security & Global Delivery (CDN Layout)

### CDN Edge Caching Map
To deliver fast app experiences worldwide, static and media files are stored in cloud object storage (AWS S3 / Google Cloud Storage) and served using CloudFront/Cloud DNS.

- **Dynamic Assets**: Secure API endpoints are routed through local Load Balancers bypassing CDNs.
- **Static Assets**: Compiled Web application code, branding kits, and static vectors are cached indefinitely across CloudFront edge instances.
- **User Attachments**: Transaction receipts and generated visual PDF balance sheets are served through private pre-signed S3 URLs expiring in 15 minutes to guarantee compliance with ISO/IEC 27001 policies.
