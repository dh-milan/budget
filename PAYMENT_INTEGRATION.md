# 💳 WealthFlow Phase 8: Complete Payment & Multi-Provider Integration Spec

This document specifies the payment flows, API integrations, and webhook processing pipelines for **WealthFlow**. The platform supports Stripe, Google Play Billing, PayPal, and regional payment providers (eSewa, Khalti) to serve users globally.

---

## 1. High-Level Payments Architecture

```
                       [ Client: Android App ]
                        │                   │
  1) Direct Checkout    │                   │ 1) Initiate Native Purchase
  (eSewa, Khalti, PayPal)                   │ (Stripe SDK, Google Play Billing)
                        ▼                   ▼
     ┌──────────────────────┐           ┌──────────────────────┐
     │ Regional Providers / │           │ Payment Provider SDK │
     │ API Gateway Handshake│           │ (App Store Gateway)  │
     └──────────┬───────────┘           └──────────┬───────────┘
                │                                  │
                │ 2) Token Verification Payload    │ 2) Send Receipt / Sub ID
                ▼                                  ▼
     ┌─────────────────────────────────────────────────────────┐
     │               WealthFlow API Backend (DRF)              │
     └──────────────────────────┬──────────────────────────────┘
                                │
                                │ 3) Cryptographic Signature Validation
                                ▼
     ┌─────────────────────────────────────────────────────────┐
     │            Stripe / Play Console Webhook Server         │
     └─────────────────────────────────────────────────────────┘
```

---

## 2. Stripe Subscriptions Integration Blueprint

Stripe is the primary credit card processing provider. Subscription lifecycles are mapped onto local user status tables, keeping permissions in sync.

### Stripe Integration Workflow
1. Client requests a new billing session: `POST /v1/payments/stripe/checkout-session/`
2. Backend creates a Stripe Checkout Session and returns the `sessionId` and `publishableKey`.
3. Client displays Stripe's payment screen using the Stripe Android SDK.
4. User completes payment. Stripe sends a `checkout.session.completed` event to the backend's webhook.
5. The backend parses the webhook signature and updates the user's subscription record to `PREMIUM`.

```python
# apps/payments/views.py
import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateStripeCheckoutSessionView(APIView):
    def post(self, request):
        try:
            # Map client reference key to database user ID
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': settings.STRIPE_PREMIUM_MONTHLY_PRICE_ID,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=settings.STRIPE_CHECKOUT_SUCCESS_URL,
                cancel_url=settings.STRIPE_CHECKOUT_CANCEL_URL,
                client_reference_id=str(request.jwt_user.id),
                metadata={
                    "user_id": str(request.jwt_user.id),
                    "tier": "PREMIUM"
                }
            )
            return Response({
                "id": session.id,
                "url": session.url
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Stripe execution failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

---

## 3. Google Play Billing Integration (Android App Client)

The mobile client integrates with the official **Google Play Billing Library** to manage native app store subscriptions.

```kotlin
// billing/PlayBillingManager.kt
package com.example.billing

import android.content.Context
import com.android.billingclient.api.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

class PlayBillingManager(private val context: Context) : PurchasesUpdatedListener {

    private var billingClient: BillingClient = BillingClient.newBuilder(context)
        .setListener(this)
        .enablePendingPurchases()
        .build()

    private val _isPremiumPurchased = MutableStateFlow(false)
    val isPremiumPurchased: StateFlow<Boolean> = _isPremiumPurchased

    fun startBillingConnection() {
        billingClient.startConnection(object : BillingClientStateListener {
            override fun onBillingSetupFinished(billingResult: BillingResult) {
                if (billingResult.responseCode == BillingClient.BillingResponseCode.OK) {
                    // Billing Client ready. Query user subscription records.
                    queryActivePurchases()
                }
            }

            override fun onBillingServiceDisconnected() {
                // Schedule reconnection attempt
            }
        })
    }

    private fun queryActivePurchases() {
        val params = QueryPurchasesParams.newBuilder()
            .setProductType(BillingClient.ProductType.SUBS)
            .build()

        billingClient.queryPurchasesAsync(params) { billingResult, purchasesList ->
            if (billingResult.responseCode == BillingClient.BillingResponseCode.OK) {
                for (purchase in purchasesList) {
                    if (purchase.purchaseState == Purchase.PurchaseState.PURCHASED) {
                        // Validate cryptographic signature on the backend before granting access
                        _isPremiumPurchased.value = true
                    }
                }
            }
        }
    }

    override fun onPurchasesUpdated(billingResult: BillingResult, purchases: MutableList<Purchase>?) {
        if (billingResult.responseCode == BillingClient.BillingResponseCode.OK && purchases != null) {
            for (purchase in purchases) {
                // Send purchase tokens to the backend API for secure validation
            }
        }
    }
}
```

---

## 4. Regional Providers Integration (eSewa & Khalti)

To serve users in global emerging markets, WealthFlow implements regional payment pathways. These systems rely on transactional token verification API handshakes:

### 1. eSewa Verification Loop (Backend Node API)
```python
# apps/payments/esewa.py
import requests
import xml.etree.ElementTree as ET

def verify_esewa_payment(amount, product_id, reference_id):
    api_url = "https://epay.esewa.com.np/epay/transrec"
    
    # Structure verification parameters according to eSewa API specifications
    payload = {
        'amt': amount,
        'scd': 'EPAY_MERCHANT_SCD',
        'rid': reference_id,
        'pid': product_id
    }
    
    try:
        response = requests.post(api_url, data=payload, timeout=10)
        
        # Parse XML response
        root = ET.fromstring(response.text)
        status_code = root.find('response_code').text.strip().lower()
        
        if status_code == 'success':
            return True
        return False
    except Exception:
        return False
```

### 2. Khalti Payment Verification
```python
# apps/payments/khalti.py
import requests

def verify_khalti_payment(token, amount_in_paisa):
    api_url = "https://khalti.com/api/v2/payment/verify/"
    headers = {
        "Authorization": "Key khalti_secret_key_123456789..."
    }
    payload = {
        "token": token,
        "amount": amount_in_paisa
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return True
        return False
    except Exception:
        return False
```
