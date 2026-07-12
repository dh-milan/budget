# 🤖 WealthFlow Phase 6: Core AI Copilot & Financial Advising Engine Spec

This document details the software architecture, prompt blueprints, parsing pipelines, and LLM orchestration methods for **WealthFlow's AI Financial Copilot**. To secure proprietary prompt strategies and protect user credentials, all LLM operations are routed through a secure Django REST Framework proxy backend.

---

## 1. High-Performance AI Request-Response Topology

```
                  ┌───────────────────────────────┐
                  │      Android Application      │ (Compose Canvas Front-End)
                  └──────────────┬────────────────┘
                                 │
                                 │ 1. HTTPS POST /v1/ai/chat/
                                 │ (User context, ledger totals, token validation)
                                 ▼
                  ┌───────────────────────────────┐
                  │    Django DRF API Gateway     │ (Request Sanitization & Rate-Limiting)
                  └──────────────┬────────────────┘
                                 │
                                 │ 2. Construct Safe Prompt Template
                                 │ (User ledger records + context injection)
                                 ▼
                  ┌───────────────────────────────┐
                  │    Google Gemini API SDK      │ (Executing gemini-1.5-pro LLM model)
                  └──────────────┬────────────────┘
                                 │
                                 │ 3. Return Raw String or Structured JSON
                                 ▼
                  ┌───────────────────────────────┐
                  │    Django DRF API Gateway     │ (Post-Processing, Audit logs, Database save)
                  └──────────────┬────────────────┘
                                 │
                                 │ 4. Send Clean Advisory Text & Chart Schemas
                                 ▼
                  ┌───────────────────────────────┐
                  │      Android Application      │ (Render dynamic Material 3 graphs)
                  └───────────────────────────────┘
```

---

## 2. LLM Prompt Construction & Financial Intelligence Context

To ensure the AI produces precise financial recommendations rather than generic boilerplate advice, the backend pulls the user's latest ledger balances and structured database details, combining them into a formatted system context:

```python
# apps/ai_copilot/prompts.py

SYSTEM_FINANCIAL_INSTRUCTIONS = """
You are a elite personal financial advisor. You hold certifications as a CFA (Chartered Financial Analyst) and CFP (Certified Financial Planner).
Your mission is to provide rigorous, accurate, actionable, and mathematically correct advisory insights to our user.

Strict Compliance Mandates:
1. Never invent user transactions or account balances. Rely only on the context provided.
2. Ensure math calculations are perfect. Cross-verify net worth, category sums, and credit card ratios.
3. Keep answers friendly, conversational, and direct. Break complex concepts into clear bullet points.
4. When identifying budget overruns or recurring expenses, provide actionable suggestions (e.g., "Adjust Food budget to $550", "Cancel duplicate subscription").
5. Format numerical values cleanly with local currency indicators ($).
6. Return a valid JSON dictionary when a structured layout is requested.
"""

def generate_user_context_prompt(user, transactions, accounts, budgets, current_message):
    # Consolidate financial accounts structure
    accounts_context = "\n".join([
        f"- {acc.name} ({acc.type}): {acc.currency} {acc.balance}" for acc in accounts
    ])

    # Consolidate historical budgets utilization
    budgets_context = "\n".join([
        f"- Category '{b.category}': Limit ${b.limit_amount}, Spent ${b.spent_amount}" for b in budgets
    ])

    # Consolidate recent transaction log
    tx_context = "\n".join([
        f"- {tx.timestamp.strftime('%Y-%m-%d')} | {tx.title} | {tx.category} | ${tx.amount} ({tx.type})"
        for tx in transactions[:15]
    ])

    full_prompt = f"""
System instructions:
{SYSTEM_FINANCIAL_INSTRUCTIONS}

Current Financial Profile of {user.full_name}:
---
ACCOUNTS:
{accounts_context}

ACTIVE BUDGET LIMITS:
{budgets_context}

RECENT TRANSACTIONS:
{tx_context}
---

User Query: "{current_message}"

Generate your response below. Include analytical explanations of spending patterns, detected anomalies (e.g. duplicate transaction charges, price increases in subscriptions), and specific recommendations:
"""
    return full_prompt
```

---

## 3. Production Gemini API REST Integration Pipeline

This service class handles connections to the Google Gemini API securely on the backend, using keys stored in backend environment variables rather than on the mobile client.

```python
# apps/ai_copilot/services.py
import os
import requests
import json
from django.conf import settings

class GeminiCopilotService:
    @staticmethod
    def query_advisor(user, prompt):
        # Using Google Gemini API endpoint securely on backend servers
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Prepare content model payloads securely
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2, # Lower values enforce logical and mathematical consistency
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }

        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            response_json = response.json()
            
            # Parse responses according to Google Generative Language schema layouts
            raw_text = response_json['candidates'][0]['content']['parts'][0]['text']
            return raw_text
            
        except Exception as e:
            raise RuntimeError(f"Gemini service pipeline failure: {str(e)}")
```

---

## 4. Advanced AI Analytical Workflows (Scheduled Celery Tasks)

### 1. Subscription & Duplicate Charge Detection
Celery background workers analyze transaction histories daily to pinpoint anomalies and unwanted subscriptions:

```python
# apps/ai_copilot/tasks.py
from celery import shared_task
from apps.ledger.models import Transaction
from apps.ai_copilot.services import GeminiCopilotService

@shared_task
def detect_duplicate_charges(user_id):
    # Query last 3 days of transaction rows
    recent_transactions = Transaction.objects.filter(
        account__user_id=user_id,
        timestamp__gte=timezone.now() - timedelta(days=3)
    )

    # Simple dictionary check for exact duplicates (Same store, same day, same amount)
    seen_charges = {}
    duplicates = []
    
    for tx in recent_transactions:
        key = (tx.title, tx.amount, tx.timestamp.date())
        if key in seen_charges:
            duplicates.append(tx)
        else:
            seen_charges[key] = tx
            
    if duplicates:
        # Generate alert and notify user via client push service
        dispatch_push_alert(user_id, "DUPLICATE_CHARGE_WARNING", f"We detected possible duplicate charges: {duplicates[0].title}")
```

### 2. Computing Financial Health Scores
Uses AI models to generate score card ratings based on saving velocities, debt structures, and budget utilization profiles:

- **Excellent (800 - 1000)**: Consistently saves $>20\%$ of monthly income, stays within budget, and pays down debt on time.
- **Fair (500 - 799)**: Stays within total budget, but has credit card APR carrying costs or minimal savings velocity.
- **Action Required (0 - 499)**: Consistently overspending budgets across primary food and leisure categories.
