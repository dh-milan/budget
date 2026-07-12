# WealthFlow Backend API

Django REST Framework backend for WealthFlow AI Personal Finance Platform.

## Quick Start

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## API Endpoints

- `/api/v1/auth/` - Authentication (Google OAuth2, JWT)
- `/api/v1/ledger/` - Accounts, transactions, categories
- `/api/v1/budgeting/` - Budgets, savings goals, debts
- `/api/v1/bills/` - Bills and payments
- `/api/v1/payments/` - Stripe subscriptions
- `/api/v1/ai/` - AI chat and insights

## Tech Stack

- Django 6.0.7 + DRF 3.17.1
- PostgreSQL + Redis
- Celery for async tasks
- Google Gemini AI
- Stripe payments
- JWT authentication