from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import (
    GoogleAuthView,
    LogoutView,
    UserProfileView,
    UserPreferencesView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
)

urlpatterns = [
    # Google OAuth2 authentication
    path('auth/google/', GoogleAuthView.as_view(), name='google-auth'),
    
    # JWT token endpoints
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('token/verify/', CustomTokenVerifyView.as_view(), name='token-verify'),
    
    # User management
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('preferences/', UserPreferencesView.as_view(), name='user-preferences'),
]