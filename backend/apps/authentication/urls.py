from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import (
    GoogleAuthView,
    LogoutView,
    UserProfileView,
    UserPreferencesView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    EmailLoginView,
    RegisterView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    EmailVerificationView,
)

urlpatterns = [
    # Google OAuth2 authentication
    path('auth/google/', GoogleAuthView.as_view(), name='google-auth'),
    
    # Email/password authentication
    path('login/', EmailLoginView.as_view(), name='email-login'),
    path('register/', RegisterView.as_view(), name='register'),
    
    # JWT token endpoints
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('token/verify/', CustomTokenVerifyView.as_view(), name='token-verify'),
    
    # User management
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('preferences/', UserPreferencesView.as_view(), name='user-preferences'),
    
    # Password reset
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset-confirm/<uid>/<token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # Email verification
    path('verify-email/<token>/', EmailVerificationView.as_view(), name='email-verify'),
]
