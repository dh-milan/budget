from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FamilyGroupViewSet,
    FamilyMemberViewSet,
    SharedBudgetViewSet,
    SharedGoalViewSet
)

router = DefaultRouter()
router.register(r'groups', FamilyGroupViewSet, basename='family-group')
router.register(r'members', FamilyMemberViewSet, basename='family-member')
router.register(r'budgets', SharedBudgetViewSet, basename='shared-budget')
router.register(r'goals', SharedGoalViewSet, basename='shared-goal')

urlpatterns = [
    path('', include(router.urls)),
]