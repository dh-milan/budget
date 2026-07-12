from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InvestmentAccountViewSet,
    InvestmentViewSet,
    PortfolioAllocationViewSet,
    InvestmentPerformanceViewSet
)

router = DefaultRouter()
router.register(r'accounts', InvestmentAccountViewSet, basename='investment-account')
router.register(r'investments', InvestmentViewSet, basename='investment')
router.register(r'portfolio', PortfolioAllocationViewSet, basename='portfolio-allocation')
router.register(r'performance', InvestmentPerformanceViewSet, basename='investment-performance')

urlpatterns = [
    path('', include(router.urls)),
]