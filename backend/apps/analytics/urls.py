from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SpendingHeatmapViewSet,
    FinancialScoreViewSet,
    ExpenseForecastViewSet,
    MonthlyReportViewSet,
    CategoryTrendViewSet,
    AnalyticsDashboardViewSet,
    AdminDashboardViewSet,
    SyncViewSet,
    NotificationCenterViewSet
)

router = DefaultRouter()
router.register(r'heatmap', SpendingHeatmapViewSet, basename='spending-heatmap')
router.register(r'financial-score', FinancialScoreViewSet, basename='financial-score')
router.register(r'forecast', ExpenseForecastViewSet, basename='expense-forecast')
router.register(r'reports', MonthlyReportViewSet, basename='monthly-report')
router.register(r'trends', CategoryTrendViewSet, basename='category-trend')
router.register(r'dashboard', AnalyticsDashboardViewSet, basename='analytics-dashboard')
router.register(r'admin', AdminDashboardViewSet, basename='admin-dashboard')
router.register(r'sync', SyncViewSet, basename='sync')
router.register(r'notifications', NotificationCenterViewSet, basename='notification-center')

urlpatterns = [
    path('', include(router.urls)),
]