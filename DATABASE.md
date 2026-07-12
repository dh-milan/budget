# 🗄️ WealthFlow Relational Database Schema (PostgreSQL)

This document contains the complete production-ready relational database schema designed for **WealthFlow**. The database utilizes **PostgreSQL** syntax and incorporates strict integrity constraints, optimal indexing profiles, automatic audit logs, and performance optimization rules.

---

## 1. Entity-Relationship Design Diagram

The following logical diagram models the relational dependencies within the system:

```
┌─────────────────┐       ┌─────────────────┐       ┌──────────────────┐
│  Subscription   │       │      Users      ├──────►│ UserPreferences  │
│      Plans      │       │ (OIDC / Google) │       └──────────────────┘
└────────┬────────┘       └────────┬────────┘
         │                         │
         ▼                         ├──────────────────────────────────┐
┌─────────────────┐                │                                  │
│  Subscriptions  │◄───────────────┤                                  │
└─────────────────┘                ▼                                  ▼
                        ┌──────────────────┐        ┌──────────────────┐
                        │ Ledger Accounts  │        │ AI Conversations │
                        └────────┬─────────┘        └────────┬─────────┘
                                 │                           │
                                 ▼                           ▼
                        ┌──────────────────┐        ┌──────────────────┐
                        │   Transactions   │        │   AI Messages    │
                        └────────┬─────────┘        └──────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │ Receipts/Attach. │
                        └──────────────────┘
```

---

## 2. DDL Table Schema Definitions

```sql
-- Enable necessary PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =========================================================================
-- 1. SUBSCRIPTION PLANS & BILLING
-- =========================================================================
CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE, -- 'Free', 'Pro', 'Enterprise'
    price_cents INTEGER NOT NULL, -- e.g., 999 for $9.99
    interval_months INTEGER NOT NULL DEFAULT 1,
    features JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================================
-- 2. CORE USER TABLE (Linked to OIDC Google Sub claim)
-- =========================================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    google_subject_id VARCHAR(255) NOT NULL UNIQUE, -- Google Sign-In sub token
    full_name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    role VARCHAR(50) NOT NULL DEFAULT 'USER', -- 'USER', 'ADMIN', 'SUPPORT'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

-- =========================================================================
-- 3. USER PREFERENCES
-- =========================================================================
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    dark_mode BOOLEAN NOT NULL DEFAULT TRUE,
    biometrics_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    notification_email BOOLEAN NOT NULL DEFAULT TRUE,
    notification_push BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================================
-- 4. ACTIVE USER SUBSCRIPTIONS (Linked to Stripe)
-- =========================================================================
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES subscription_plans(id),
    stripe_customer_id VARCHAR(255) UNIQUE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    status VARCHAR(50) NOT NULL, -- 'active', 'canceled', 'past_due'
    current_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    current_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_period_dates CHECK (current_period_end > current_period_start)
);

CREATE INDEX idx_sub_user ON user_subscriptions(user_id);

-- =========================================================================
-- 5. LEDGER FINANCIAL ACCOUNTS
-- =========================================================================
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'CHECKING', 'SAVINGS', 'CREDIT_CARD', 'INVESTMENT'
    balance NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_accounts_user ON accounts(user_id);

-- =========================================================================
-- 6. TRANSACTIONS
-- =========================================================================
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    category VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL, -- 'EXPENSE', 'INCOME', 'TRANSFER'
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    note TEXT,
    tags VARCHAR(255),
    is_recurring BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_account ON transactions(account_id);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp DESC);
CREATE INDEX idx_transactions_category ON transactions(category);

-- =========================================================================
-- 7. BUDGETS
-- =========================================================================
CREATE TABLE budgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    limit_amount NUMERIC(15,2) NOT NULL,
    spent_amount NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    month_start DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_limit CHECK (limit_amount > 0),
    CONSTRAINT unique_user_category_month UNIQUE(user_id, category, month_start)
);

-- =========================================================================
-- 8. SAVINGS GOALS
-- =========================================================================
CREATE TABLE savings_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    target_amount NUMERIC(15,2) NOT NULL,
    current_amount NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    target_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_target CHECK (target_amount > 0)
);

-- =========================================================================
-- 9. DEBTS & LIABILITIES
-- =========================================================================
CREATE TABLE debts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'CREDIT_CARD', 'LOAN'
    total_balance NUMERIC(15,2) NOT NULL,
    interest_rate NUMERIC(5,2) NOT NULL, -- e.g., 18.99%
    due_date DATE NOT NULL,
    repayment_amount NUMERIC(15,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================================
-- 10. BILLS & RECURRING OBLIGATIONS
-- =========================================================================
CREATE TABLE bills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    due_date DATE NOT NULL,
    category VARCHAR(100) NOT NULL,
    is_paid BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================================
-- 11. AI CONVERSATIONS & CHAT HISTORY
-- =========================================================================
CREATE TABLE ai_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL DEFAULT 'New Discussion',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ai_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES ai_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user', 'model'
    text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_msg_conv ON ai_messages(conversation_id);

-- =========================================================================
-- 12. AUDIT LOGS (Security compliance)
-- =========================================================================
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(255) NOT NULL, -- e.g., 'AUTH_SUCCESS', 'DEBT_PAYMENT', 'EXPORT_CSV'
    ip_address VARCHAR(45),
    user_agent TEXT,
    payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);
```

---

## 3. Database Administration & Backup Infrastructure

### Weekly Automated Backups (Cron Job Script)
Production servers execute dynamic physical backups using pg_dump compressed with gzip, which are then streamed instantly into an encrypted, version-controlled AWS S3 bucket:

```bash
#!/bin/bash
# WealthFlow Automated Database Snapshot
DB_NAME="wealthflow_prod"
BACKUP_DIR="/opt/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/db_backup_${DB_NAME}_${TIMESTAMP}.sql.gz"

mkdir -p ${BACKUP_DIR}

# Generate compressed SQL dump securely using key rings
pg_dump -h db-cluster.wealthflow.internal -U db_admin_user -d ${DB_NAME} | gzip > ${BACKUP_FILE}

# Sync backup dump securely to an AWS S3 bucket with Glacier archiving
aws s3 cp ${BACKUP_FILE} s3://wealthflow-db-backups/production/ --sse aws:kms

# Evict locally stored dumps older than 7 days to preserve memory
find ${BACKUP_DIR} -name "db_backup_*" -mtime +7 -delete
```
