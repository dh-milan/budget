# 🖥️ WealthFlow Phase 9: Enterprise Admin Console Specification

This document details the architecture, design layout, database audit procedures, and security controls for the **WealthFlow Enterprise Admin Console**.

---

## 1. System Topology & UI Layout

The Web Admin Console is built as a Single Page Application (SPA) using React, Tailwind CSS, and TypeScript, communicating with the Django REST Framework API through secure, role-restricted admin routes (`/v1/admin/*`).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        WealthFlow Admin Dashboard                      │
├────────────────────────────────────────────────────────────────────────┤
│  [Navigation Drawer]        [Metric Cards Block]                       │
│  ├─ System Telemetry        ┌──────────────┐ ┌──────────────┐          │
│  ├─ User Management         │ Active Users │ │ Monthly Rev  │          │
│  ├─ Subscription Tier       │    45,820    │ │   $389,450   │          │
│  ├─ AI Usage Metrics        └──────────────┘ └──────────────┘          │
│  ├─ Fraud Analysis                                                     │
│  ├─ Audit Logs             [Interactive Live Analytics Graph]          │
│                             ┌────────────────────────────────┐         │
│                             │  / - - - \                     │         │
│                             │ /         \                    │         │
│                             └────────────────────────────────┘         │
│                                                                        │
│  [Recent Audit Events Log Table]                                       │
│  ┌───────────┬───────────────────────────────┬──────────────────────┐  │
│  │ Timestamp │ User Ident                    │ Flagged Action       │  │
│  ├───────────┼───────────────────────────────┼──────────────────────┤  │
│  │ 08:21:44  │ alex.rivera@gmail.com (OIDC)  │ EXPORT_CSV (Success) │  │
│  │ 08:19:12  │ system.celery.task            │ BILLS_PREDICTED (72) │  │
│  └───────────┴───────────────────────────────┴──────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Key Administrative Dashboards

### 1. User & Subscription Analytics Profile
- **Target Tracking**: Track active subscriptions, cancellations (churn rates), and upgrades in real-time.
- **Actions**: Trigger hard limits on delinquent billing cycles or manually issue temporary premium passes for VIP support tickets.

### 2. Fraud & Security Monitoring Hub
- **Target Tracking**: Scans metadata including login IP regions, frequency thresholds, and extreme transaction modifications.
- **Actions**: Temporarily lock profiles or revoke Google Identity OIDC access tokens instantly if a login bypass attempt is flagged by the security engine.

### 3. AI Performance & Token Metric Telemetry
- **Target Tracking**: Records API latency and token usage volumes for Google Gemini and OpenAI models.
- **Actions**: Configure dynamic fallback switches or adjust user-specific AI message rate limits to avoid server overruns.

---

## 3. High-Performance REST API Endpoint Definitions (DRF)

Only accounts with the `role = 'ADMIN'` or `'SUPPORT'` claim in their JWT can access these endpoints.

### 1. Retrieve System Operational Telemetry
* **`GET /v1/admin/telemetry/`**:
  - **Headers**: `Authorization: Bearer <ADMIN_JWT_TOKEN>`
  - **Response**:
    ```json
    {
      "database": {
        "status": "healthy",
        "active_connections": 14,
        "replica_lag_ms": 1.2
      },
      "redis": {
        "status": "healthy",
        "used_memory_human": "48.2MB"
      },
      "celery": {
        "active_workers": 4,
        "queued_tasks": 0
      }
    }
    ```

### 2. Manual Account Limitation / Flagging
* **`POST /v1/admin/users/{id}/suspend/`**:
  - **Headers**: `Authorization: Bearer <ADMIN_JWT_TOKEN>`
  - **Payload**:
    ```json
    {
      "reason": "Suspicious login velocity from multi-regional IPs",
      "blacklist_duration_hours": 24
    }
    ```
  - **Response**:
    ```json
    {
      "user_id": "usr_90a12",
      "status": "SUSPENDED",
      "expires_at": "2026-07-13T08:19:07Z"
    }
    ```

---

## 4. Secure Auditing & DB Triggers (SQL)

To satisfy enterprise financial compliance policies (e.g. SOC 2), every modification to transaction records or user roles triggers automatic insertions into the `audit_logs` persistence database using a SQL procedure:

```sql
-- Create automatic trigger procedure for user role changes
CREATE OR REPLACE FUNCTION audit_user_role_modifications()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.role <> NEW.role THEN
        INSERT INTO audit_logs (user_id, action, ip_address, user_agent, payload)
        VALUES (
            NEW.id,
            'USER_ROLE_UPGRADE',
            'SYSTEM_ADMIN_API',
            'WealthFlow Admin Gateway',
            jsonb_build_object(
                'previous_role', OLD.role,
                'new_role', NEW.role,
                'modified_at', CURRENT_TIMESTAMP
            )
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_audit_user_roles
AFTER UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION audit_user_role_modifications();
```
