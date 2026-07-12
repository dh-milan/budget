# 🛡️ WealthFlow Production Hardening & Launch Checklist

This document compiles the exhaustive security hardening configurations, Stripe payment webhook implementation guidelines, and Google Play Store release preparations required for **WealthFlow**.

---

## 1. Security Infrastructure & Cryptographic Hardening

### Android Keystore & Room Database Encryption (SQLCipher)
To secure the client database from offline hardware extractions, SQLite/Room databases must be encrypted in production using SQLCipher.

```kotlin
// In production AppDatabase.kt configuration:
val factory = SupportFactory(SQLiteDatabase.getBytes("SecurePassphraseOrUserUUID".toCharArray()))
val database = Room.databaseBuilder(context, AppDatabase::class.java, "wealthflow.db")
    .openHelperFactory(factory) // Automatically encrypts database pages
    .build()
```

### SSL Pinning Specification (`network_security_config.xml`)
To defend against Man-In-The-Middle (MITM) attacks and proxy packet captures, SSL/TLS certificate pinning is enforced in the Android network layout.

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="false">
        <domain includeSubdomains="true">api.wealthflow.internal</domain>
        <pin-set expiration="2027-01-01">
            <!-- Leaf Certificate Pin -->
            <pin digest="SHA-256">9b82f02da...=</pin>
            <!-- Backup Intermediate Certificate Pin -->
            <pin digest="SHA-256">a836dc2f4...=</pin>
        </pin-set>
    </domain-config>
</network-security-config>
```

---

## 2. Secure Stripe Billing Webhook Receiver (DRF Python)

The Django API handles recurring subscription lifecycle payments securely via verified webhook signing events sent directly from Stripe.

```python
import stripe
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import UserSubscription, UserProfile

stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.STRIPE_WEBHOOK_SIGNING_SECRET

@csrf_exempt
def stripe_billing_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        # Cryptographically verify that this webhook originated from Stripe
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Process events
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # Locate user profile from metadata
        user_id = session['client_reference_id']
        stripe_sub_id = session['subscription']
        stripe_customer_id = session['customer']
        
        # Provision Premium plan features instantly
        sub = UserSubscription.objects.get_or_create(user_id=user_id)
        sub.stripe_subscription_id = stripe_sub_id
        sub.stripe_customer_id = stripe_customer_id
        sub.status = "active"
        sub.save()

    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        # Handle subscription failure states (Downgrade user permissions)
        stripe_sub_id = invoice['subscription']
        sub = UserSubscription.objects.get(stripe_subscription_id=stripe_sub_id)
        sub.status = "past_due"
        sub.save()

    return HttpResponse(status=200)
```

---

## 3. Production Release Checklist

### Phase 1: Security & Compliance
- [ ] **Data Encryption**: Turn on Android EncryptedSharedPreferences and compile Room Database with SQLCipher.
- [ ] **Certificate Pinning**: Verify `network_security_config.xml` is fully referenced inside your `AndroidManifest.xml`.
- [ ] **OWASP Mobile Compliance**: Block execution if the application detects that the host device is rooted or runs a debugger emulator in production.
- [ ] **ProGuard Rules**: Keep model classes safe from obfuscation while optimizing the remaining bytecode to protect IP from reverse engineering.
- [ ] **OAuth Client Consent**: Register SHA-256 App signing keys in the Google Cloud/Firebase console to authorize native Google Authentication flow.

### Phase 2: Billing & Monitization
- [ ] **Stripe Production Verification**: Switch API credentials from `test` to `live` (i.e. swap keys starting with `pk_test` to `pk_live`).
- [ ] **Play Store Billing Config**: Map all Play Console in-app products to subscription parameters on the backend.
- [ ] **Grace Period Management**: Program local caches to allow offline feature verification up to 72 hours if server validation is interrupted.

### Phase 3: Android App Bundling & Play Console Deployment
- [ ] **Build Optimization**: Generate the optimized production deployment package (`.aab` - Android App Bundle) rather than `.apk`.
  ```bash
  gradle :app:bundleRelease
  ```
- [ ] **Version Auto-Incrementing**: Increment both the `versionCode` and `versionName` strings inside `app/build.gradle.kts`.
- [ ] **Launcher Adaptive Icons**: Verify adaptive icons (`ic_launcher_foreground.png` and background coordinates) are fully set.
- [ ] **Store Listing Copy**: Write localization files for multi-country support on the Play Store, illustrating strict data privacy statements.
- [ ] **Compliance Form (Data Safety)**: Accurately complete the Play Console Data Safety questionnaire explicitly listing that the app utilizes HTTPS transfers and does not share personal details with third parties.
