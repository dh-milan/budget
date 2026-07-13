# Backend-Frontend Connection Setup

## Overview
This document describes the changes made to connect the WealthFlow Android app (frontend) to the Django backend.

## Changes Made

### 1. Backend Configuration

#### CORS Configuration (`backend/wealthflow/settings.py`)
- Added `http://192.168.1.68:8000` to `CORS_ALLOWED_ORIGINS` to allow Android app access
- Enabled `CORS_ALLOW_CREDENTIALS = True` for authenticated requests

#### Authentication Endpoints (`backend/apps/authentication/`)

**New Views Added:**
- `EmailLoginView`: Standard email/password authentication endpoint
  - Endpoint: `POST /api/v1/auth/login/`
  - Returns JWT access and refresh tokens
  - Validates credentials and logs authentication events

- `RegisterView`: User registration endpoint
  - Endpoint: `POST /api/v1/auth/register/`
  - Creates new user with email/password
  - Returns JWT tokens on successful registration
  - Validates password length (minimum 8 characters)
  - Checks for duplicate emails

**Updated URLs (`backend/apps/authentication/urls.py`):**
```python
urlpatterns = [
    path('auth/google/', GoogleAuthView.as_view(), name='google-auth'),
    path('login/', EmailLoginView.as_view(), name='email-login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('token/verify/', CustomTokenVerifyView.as_view(), name='token-verify'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('preferences/', UserPreferencesView.as_view(), name='user-preferences'),
]
```

### 2. Frontend Configuration

#### API Service Layer (`app/src/main/java/com/example/data/api/`)

**RetrofitClient.kt:**
- Added `authToken` variable to store JWT token globally
- Implemented `authInterceptor` to automatically attach Bearer token to all requests
- Token is now automatically included in request headers

**FinanceApiService.kt:**
- Updated login endpoint: `POST auth/login/` (changed from `auth/token/`)
- Added register endpoint: `POST auth/register/`
- Removed manual `@Header("Authorization")` parameters (now handled by interceptor)
- Added `UserData` model for user information
- Added `RegisterRequest` model for registration
- Updated `LoginResponse` to include user data

#### ViewModel Integration (`app/src/main/java/com/example/ui/viewmodel/FinanceViewModel.kt`)

**Added Methods:**
- `login(email, password)`: Authenticates user with backend
  - Stores JWT token in RetrofitClient
  - Loads data from backend after successful login
  - Shows success/error toast messages

- `register(name, email, password)`: Registers new user
  - Creates account via backend API
  - Stores JWT token
  - Loads initial data from backend

**Updated Methods:**
- `loadDataFromBackend()`: Now uses automatic token attachment (removed manual header parameter)

#### UI Integration (`app/src/main/java/com/example/ui/screens/AuthScreen.kt`)

**LoginScreen:**
- Added `FinanceViewModel` instance
- Connected login button to `financeViewModel.login()`
- Shows success toast after calling ViewModel

**RegisterScreen:**
- Added `FinanceViewModel` instance
- Connected register button to `financeViewModel.register()`
- Removed duplicate success toast (now handled by ViewModel)

### 3. Data Flow

#### Authentication Flow
```
User enters credentials
    ↓
UI calls ViewModel.login() or ViewModel.register()
    ↓
ViewModel makes API call via Retrofit
    ↓
Auth interceptor adds Bearer token to request
    ↓
Backend validates credentials
    ↓
Backend returns JWT tokens (access + refresh)
    ↓
ViewModel stores token in RetrofitClient.authToken
    ↓
ViewModel loads data from backend
    ↓
Success/error toast shown to user
```

#### Data Synchronization Flow
```
User logs in successfully
    ↓
ViewModel calls loadDataFromBackend()
    ↓
API request sent with JWT token in header
    ↓
Backend validates token
    ↓
Backend returns user's transactions
    ↓
ViewModel saves transactions to local database
    ↓
UI observes database changes and updates
```

### 4. API Endpoints Available

#### Authentication
- `POST /api/v1/auth/login/` - Email/password login
- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/auth/google/` - Google OAuth login
- `POST /api/v1/auth/token/refresh/` - Refresh access token
- `POST /api/v1/auth/token/verify/` - Verify token
- `POST /api/v1/auth/logout/` - Logout (blacklist token)

#### Ledger/Transactions
- `GET /api/v1/ledger/transactions/` - Get all transactions
- `POST /api/v1/ledger/transactions/` - Create transaction
- `GET /api/v1/ledger/accounts/` - Get accounts
- `GET /api/v1/ledger/categories/` - Get categories
- `GET /api/v1/ledger/net-worth/` - Get net worth
- `GET /api/v1/ledger/cash-flow/` - Get cash flow report

### 5. Network Configuration

**Backend URL:** `http://192.168.1.68:8000/api/v1/`

**Requirements:**
- Backend server must be running on the same network
- Phone/emulator must be able to reach `192.168.1.68:8000`
- CORS is configured to allow this origin

### 6. Testing the Connection

1. **Start the Backend:**
   ```bash
   cd backend
   python manage.py runserver 0.0.0.0:8000
   ```

2. **Run the Android App:**
   ```bash
   cd app
   ./gradlew installDebug
   ```

3. **Test Login:**
   - Open app
   - Enter email and password
   - Click "Sign In"
   - Check backend logs for authentication request
   - Verify data loads from backend

4. **Test Registration:**
   - Navigate to "Sign Up"
   - Fill in name, email, password
   - Click "Create Account"
   - Verify account is created in backend
   - Verify automatic login after registration

### 7. Security Features

- JWT tokens with 15-minute access token lifetime
- 30-day refresh token lifetime
- Automatic token refresh
- Token blacklisting on logout
- Password hashing using Django's password validators
- CORS configured for specific origins only
- Audit logging for all authentication events
- Login history tracking

### 8. Error Handling

- Network errors: App continues with local data
- Invalid credentials: Shows error toast
- Backend unavailable: Graceful fallback to local-only mode
- Token expiration: Automatic refresh attempted

## Next Steps

1. **Create Test Users:**
   ```bash
   cd backend
   python manage.py createsuperuser
   ```

2. **Configure Email:**
   - Update email settings in `.env` for password reset emails

3. **Add More Endpoints:**
   - Budget management
   - Goals tracking
   - Debt management
   - Bill payments
   - Receipt scanning

4. **Implement Offline Sync:**
   - Queue changes when offline
   - Sync when connection restored
   - Conflict resolution

5. **Add Push Notifications:**
   - Bill reminders
   - Budget alerts
   - Goal progress updates

## Troubleshooting

### Backend Not Reachable
- Ensure backend is running: `python manage.py runserver 0.0.0.0:8000`
- Check firewall allows port 8000
- Verify phone and computer are on same network
- Test with browser: `http://192.168.1.68:8000/api/v1/auth/login/`

### CORS Errors
- Verify `CORS_ALLOWED_ORIGINS` includes your app's origin
- Check backend logs for CORS errors
- Ensure `corsheaders` is in `INSTALLED_APPS`

### Authentication Fails
- Check backend logs for authentication attempts
- Verify user exists in database
- Ensure password is correctly hashed
- Check JWT token configuration

### Data Not Loading
- Verify JWT token is being sent in request headers
- Check backend logs for token validation
- Ensure user has transactions in database
- Check network response in Android Studio Logcat