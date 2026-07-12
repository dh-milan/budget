from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ExpenseGroupViewSet,
    GroupMemberViewSet,
    SplitExpenseViewSet,
    SettlementViewSet
)

router = DefaultRouter()
router.register(r'groups', ExpenseGroupViewSet, basename='expense-group')
router.register(r'members', GroupMemberViewSet, basename='group-member')
router.register(r'expenses', SplitExpenseViewSet, basename='split-expense')
router.register(r'settlements', SettlementViewSet, basename='settlement')

urlpatterns = [
    path('', include(router.urls)),
]