# 🌐 WealthFlow Enterprise Architecture Specification

This document details the multi-tier production-ready architecture of **WealthFlow**, a commercial-grade personal finance and AI-driven wealth advisory platform. The system is designed to provide high-performance, offline-first mobile operations combined with an enterprise backend capable of processing millions of transactions and secure real-time AI analyses.

---

## 1. High-Level Architecture Topology

WealthFlow employs a distributed micro-services and event-driven architecture designed for $99.99\%$ availability, minimal latency, and robust offline capabilities.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Jetpack Compose Client                          │
│                                                                        │
│   ┌───────────────────────┐            ┌──────────────────────────┐    │
│   │   MainAppScreen (UI)  │◄──────────►│  FinanceViewModel (State)│    │
│   └───────────────────────┘            └───────────┬──────────────┘    │
│                                                    │                   │
│   ┌───────────────────────┐            ┌───────────▼──────────────┐    │
│   │   Local SQLite (Room) │◄──────────►│  FinanceRepository (Data)│    │
│   └───────────────────────┘            └───────────┬──────────────┘    │
└────────────────────────────────────────────────────┼───────────────────┘
                                                     │ (Secure HTTPS / JWT)
                                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        AWS Cloud Environment                           │
│                                                                        │
│                      ┌───────────────────────────┐                     │
│                      │    Application Gateway    │                     │
│                      │ (AWS ALB / Nginx Proxy)   │                     │
│                      └─────────────┬─────────────┘                     │
│                                    │                                   │
│             ┌──────────────────────┴──────────────────────┐            │
│             ▼                                             ▼            │
│  ┌───────────────────────┐                     ┌────────────────────┐  │
│  │  DRF App Service 1    │                     │ DRF App Service 2  │  │
│  └──────────┬────────────┘                     └──────────┬─────────┘  │
│             │                                             │            │
│             └──────────────────────┬──────────────────────┘            │
│                                    │                                   │
│             ┌──────────────────────┼──────────────────────┐            │
│             ▼                      ▼                      ▼            │
│  ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐  │
│  │   Redis Cache &    │ │    PostgreSQL      │ │   Celery Workers   │  │
│  │   Broker Queue     │ │ (Aurora Serverless)│ │   (Ecs Fargate)    │  │
│  └────────────────────┘ └────────────────────┘ └────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

### Key Tiers

1. **Client Tier (Android Native)**:
   - Built using **Kotlin**, **Jetpack Compose**, and **Material 3**.
   - Employs **MVVM (Model-View-ViewModel)** with **Clean Architecture** boundaries.
   - Powered by an **Offline-First local storage engine (Room Database)**. The repository coordinates state, utilizing local SQLite caches before sync.

2. **Web Gateway & Application Layer (DRF Backend)**:
   - Written in **Python / Django REST Framework (DRF)**.
   - Exposes RESTful API endpoints secured by OAuth 2.0 and state-of-the-art JWT (JSON Web Tokens).
   - Handles account syncing, billing webhooks, administrative workflows, and secure gateway proxying to the Gemini/OpenAI API.

3. **In-Memory Cache & Broker (Redis & Celery)**:
   - **Redis** manages real-time caching of transaction histories, rate-limit counters, and active session tokens.
   - Also serves as the primary message broker for **Celery**, facilitating background task workers that execute statement parsing, scheduled bill predictions, and duplicate transaction scans.

4. **Persistence Layer (PostgreSQL)**:
   - Uses an **AWS Aurora PostgreSQL** cluster configured with automatic partitioning, point-in-time recovery (PITR), and reader replicas to service analytical queries asynchronously.

---

## 2. Secure Google Sign-In & JWT Lifecycle

WealthFlow completely avoids custom password credential management to mitigate security risks. The app relies on **Google Identity Services** integrated with **Firebase Authentication** or direct OpenID Connect (OIDC).

### Authentication Protocol Flow

```
Mobile App (Compose)          Google Identity SDK            WealthFlow Backend
       │                              │                             │
       │ 1. Request Sign-In           │                             │
       ├─────────────────────────────►│                             │
       │                              │                             │
       │ 2. Prompt Account Chooser    │                             │
       │◄─────────────────────────────┤                             │
       │                              │                             │
       │ 3. Sign-In Successful        │                             │
       │    (IdToken Returned)        │                             │
       ├─────────────────────────────►│                             │
       │                                                            │
       │ 4. Send IdToken via HTTPS POST /v1/auth/google             │
       ├───────────────────────────────────────────────────────────►│
       │                                                            │ 5. Verify IdToken
       │                                                            │    via Google API
       │                                                            │ 6. Find or Create User
       │                                                            │ 7. Generate JWT &
       │                                                            │    Refresh Token
       │ 8. Access Token & Refresh Token returned                   │
       │◄───────────────────────────────────────────────────────────┤
       │                                                            │
       │ 9. Save JWT to Secure Encrypted SharedPreferences/KeyStore│
       ▼                                                            ▼
```

### JWT Security Specs
- **Access Tokens**: Short-lived (15 minutes). Decoded stateless tokens containing role claims, subscription tiers, and unique user identifiers.
- **Refresh Tokens**: Long-lived (30 days). Securely stored inside an encrypted PostgreSQL table linked to active user devices. Rotated on every single usage to prevent replay attacks.
- **Header Structure**:
  ```http
  Authorization: Bearer <JWT_ACCESS_TOKEN>
  ```

---

## 3. Production API Reference Spec

All REST requests must possess the header: `Accept: application/json` and `Content-Type: application/json`.

### 1. Authentication
* **`POST /v1/auth/google/`**:
  - **Payload**: `{ "id_token": "eyJhbGciOiJ..." }`
  - **Response**:
    ```json
    {
      "access": "eyJhbGciOi...",
      "refresh": "eyJhbGciOi...",
      "user": {
        "id": "usr_90a12",
        "email": "user@gmail.com",
        "name": "Alex Rivera",
        "tier": "PREMIUM"
      }
    }
    ```

### 2. Ledger Accounts & Transactions
* **`GET /v1/transactions/`**:
  - Retrieves transactions list (supports cursor-based pagination for high performance).
* **`POST /v1/transactions/`**:
  - Creates a new financial ledger transaction.
  - **Payload**:
    ```json
    {
      "title": "Aesthetic Coffee Shop",
      "amount": 6.50,
      "category": "Food",
      "type": "EXPENSE",
      "note": "Organic cold brew",
      "tags": "Coffee, Work"
    }
    ```

### 3. AI Copilot Gateway
* **`POST /v1/ai/chat/`**:
  - Sends context and questions to the AI assistant.
  - **Payload**:
    ```json
    {
      "message": "Analyze my spending for last month and suggest a budget limit."
    }
    ```
  - **Response**:
    ```json
    {
      "reply": "Your food expenses were $620 (12% over limit). I recommend a dynamic food budget of $550 with automated alert triggers at 80% utilization.",
      "suggestions": ["Set Food budget to $550", "View Food transactions"]
    }
    ```

---

## 4. Developer Quickstart Guide

### Client Configuration
1. Clone the project and verify your Android SDK matches **API Level 34+**.
2. Run `compile_applet` to execute the Gradle build.
3. To configure the direct Gemini AI gateway or your backend URL:
   - Edit the `.env` configuration file (created automatically from `.env.example`).
   - Enter your actual Gemini API token in **AI Studio Secrets**.

### Local JVM Unit and Screenshot Testing
WealthFlow enforces a strict testing harness using local JVM configurations to bypass heavy emulator runtimes:
```bash
# Execute local unit and Robolectric functional tests
gradle :app:testDebugUnitTest

# Run Roborazzi visual screenshot tests
gradle :app:verifyRoborazziDebug
```
For visual regression changes:
```bash
# Re-record screenshot baselines
gradle :app:recordRoborazziDebug
```

---

## 5. End-User Guide: Key Features

1. **Dashboard Tab**: Provides a comprehensive "Bento Grid" visualization of Net Worth, recent expenditure trends (rendered natively using dynamic Compose Canvas), and active savings progression bars.
2. **Ledger Tab**: Displays chronological transaction entries with real-time balance sheets. Items can be exported instantly to CSV format via the **Share** button.
3. **Budgets Tab**: Tracks custom budgets per category (e.g. food, rent) and targets savings.
4. **Bills & Debt Tab**: Schedules future bills and maps credit cards and loans with dynamic APR calculators.
5. **AI Advisor Tab**: A premium natural-language interface communicating with the AI to perform portfolio audits and receive automated budget strategies.
