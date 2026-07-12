from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TwoFactorAuthViewSet,
    DeviceViewSet,
    SessionViewSet,
    LoginHistoryViewSet,
    BiometricAuthViewSet,
    SecurityDashboardViewSet
)

router = DefaultRouter()
router.register(r'2fa', TwoFactorAuthViewSet, basename='two-factor')
router.register(r'devices', DeviceViewSet, basename='device')
router.register(r'sessions', SessionViewSet, basename='session')
router.register(r'login-history', LoginHistoryViewSet, basename='login-history')
router.register(r'biometric', BiometricAuthViewSet, basename='biometric')
router.register(r'dashboard', SecurityDashboardViewSet, basename='security-dashboard')

urlpatterns = [
    path('', include(router.urls)),
]