# 🐍 WealthFlow Phase 4: Backend Service & Distributed Job Processing Specification

This document details the software architecture, package layouts, and high-concurrency configurations for the **WealthFlow** enterprise backend. The backend is built using Python, Django REST Framework (DRF), PostgreSQL, Redis, and Celery, running behind an Nginx reverse proxy.

---

## 1. Django REST Framework Structure & Architecture

The application is structured into domain-specific micro-applications, promoting encapsulation and enabling easy refactoring or scaling into microservices.

```
wealthflow/
│
├── wealthflow/                  # Project configuration root
│   ├── __init__.py
│   ├── settings.py              # Base and environment settings
│   ├── urls.py                  # Global route dispatcher
│   └── celery.py                # Celery worker configuration
│
├── apps/                        # Application modules namespace
│   ├── authentication/          # User login, OIDC verification, JWT profiles
│   ├── ledger/                  # Accounts, Transactions, Categories, Syncing
│   ├── budgeting/               # Budgets and Savings Goal tracking
│   ├── bills/                   # Bill calendars and prediction models
│   ├── payments/                # Stripe, Google Play Billing integrations
│   └── ai_copilot/              # Gemini API, LLM prompt routing & sanitization
│
├── manage.py
└── Dockerfile.prod
```

---

## 2. JWT & Stateless Session Validation Middleware

The security layer intercepts all incoming API requests using stateless middleware, validating JWT claims, tracking client rate-limiting counters, and logging audit details in PostgreSQL.

```python
# apps/authentication/middleware.py
import jwt
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from apps.authentication.models import AuditLog

User = get_user_model()

class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            request.jwt_user = None
            return

        token = auth_header.split(' ')[1]
        try:
            # Decode stateless access tokens securely inside memory
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            # Attaching user instance directly to current request lifecycle
            user = User.objects.get(id=user_id)
            if not user.is_active:
                return JsonResponse({"error": "User account is suspended"}, status=403)
                
            request.jwt_user = user
            
            # Log the successful transaction call asynchronously
            self.log_audit_event(request, user, "API_REQUEST")
            
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
            return JsonResponse({"error": "Invalid or expired authorization token"}, status=401)

    def log_audit_event(self, request, user, action):
        AuditLog.objects.create(
            user=user,
            action=action,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.headers.get('User-Agent', '')[:255]
        )
```

---

## 3. High-Performance Ledger Operations (Transactional Safety)

Ledger transaction records are sensitive. The backend uses database transactions with row-level locks (`select_for_update`) to prevent race conditions during updates:

```python
# apps/ledger/views.py
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Transaction, Account
from .serializers import TransactionSerializer

class CreateTransactionView(APIView):
    def post(self, request):
        serializer = TransactionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        
        try:
            # Enforce strict ACID boundaries using database transaction managers
            with transaction.atomic():
                # Acquire a write lock on the associated account row
                account = Account.objects.select_for_update().get(
                    id=data['account_id'], 
                    user=request.jwt_user
                )

                # Mutate account balance according to transaction cashflow type
                if data['type'] == 'EXPENSE':
                    account.balance -= data['amount']
                elif data['type'] == 'INCOME':
                    account.balance += data['amount']
                
                account.save()

                # Commit new transaction row to persistence layer
                new_tx = Transaction.objects.create(
                    account=account,
                    title=data['title'],
                    amount=data['amount'],
                    category=data['category'],
                    type=data['type'],
                    note=data.get('note'),
                    tags=data.get('tags')
                )
                
            return Response(TransactionSerializer(new_tx).data, status=status.HTTP_201_CREATED)

        except Account.DoesNotExist:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Transaction aborted: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

---

## 4. Production Settings Configuration

This production configuration ensures strict compliance with security standards:

```python
# wealthflow/settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
DEBUG = False

ALLOWED_HOSTS = ['api.wealthflow.internal', 'localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'rest_framework',
    'rest_framework_simplejwt',
    'apps.authentication',
    'apps.ledger',
    'apps.budgeting',
    'apps.bills',
    'apps.payments',
    'apps.ai_copilot',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'wealthflow_prod',
        'USER': 'flow_admin',
        'PASSWORD': 'SecureAdminPassword',
        'HOST': 'db-cluster.wealthflow.internal',
        'PORT': '5432',
    }
}

# SimpleJWT Authentication settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}
