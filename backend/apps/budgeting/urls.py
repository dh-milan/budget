from django.urls import path
from .views import (
    BudgetListView,
    BudgetDetailView,
    SavingsGoalListView,
    SavingsGoalDetailView,
    DebtListView,
    DebtDetailView,
    BudgetSummaryView,
    SavingsSummaryView,
    DebtSummaryView,
)

urlpatterns = [
    # Budget endpoints
    path('budgets/', BudgetListView.as_view(), name='budget-list'),
    path('budgets/<uuid:budget_id>/', BudgetDetailView.as_view(), name='budget-detail'),
    path('budgets/summary/', BudgetSummaryView.as_view(), name='budget-summary'),
    
    # Savings goals endpoints
    path('savings-goals/', SavingsGoalListView.as_view(), name='savings-goal-list'),
    path('savings-goals/<uuid:goal_id>/', SavingsGoalDetailView.as_view(), name='savings-goal-detail'),
    path('savings-goals/summary/', SavingsSummaryView.as_view(), name='savings-summary'),
    
    # Debt endpoints
    path('debts/', DebtListView.as_view(), name='debt-list'),
    path('debts/<uuid:debt_id>/', DebtDetailView.as_view(), name='debt-detail'),
    path('debts/summary/', DebtSummaryView.as_view(), name='debt-summary'),
]