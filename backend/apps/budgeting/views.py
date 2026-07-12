from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Budget, SavingsGoal, Debt
from .serializers import (
    BudgetSerializer, BudgetCreateSerializer,
    SavingsGoalSerializer, SavingsGoalCreateSerializer,
    DebtSerializer, DebtCreateSerializer,
    BudgetSummarySerializer, SavingsSummarySerializer, DebtSummarySerializer
)
from apps.authentication.models import AuditLog


class BudgetListView(APIView):
    """List and create budgets"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        month = request.query_params.get('month')
        budgets = Budget.objects.filter(user=request.user, is_active=True)
        
        if month:
            # Parse month (format: YYYY-MM)
            year, month_num = month.split('-')
            budgets = budgets.filter(month_start__year=int(year), month_start__month=int(month_num))
        
        serializer = BudgetSerializer(budgets, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = BudgetCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Set month_start to first day of month if not provided
            month_start = serializer.validated_data.get('month_start')
            if not month_start:
                month_start = timezone.now().date().replace(day=1)
            else:
                month_start = month_start.replace(day=1)
            
            budget = serializer.save(user=request.user, month_start=month_start)
            
            AuditLog.objects.create(
                user=request.user,
                action='BUDGET_CREATE',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={'budget_id': str(budget.id), 'category': budget.category}
            )
            
            return Response(
                BudgetSerializer(budget).data, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class BudgetDetailView(APIView):
    """Get, update, and delete budgets"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, budget_id):
        try:
            budget = Budget.objects.get(id=budget_id, user=request.user)
            serializer = BudgetSerializer(budget)
            return Response(serializer.data)
        except Budget.DoesNotExist:
            return Response(
                {"error": "Budget not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def patch(self, request, budget_id):
        try:
            budget = Budget.objects.get(id=budget_id, user=request.user)
            serializer = BudgetCreateSerializer(budget, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                
                AuditLog.objects.create(
                    user=request.user,
                    action='BUDGET_UPDATE',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                    payload={'budget_id': str(budget.id)}
                )
                
                return Response(BudgetSerializer(budget).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Budget.DoesNotExist:
            return Response(
                {"error": "Budget not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, budget_id):
        try:
            budget = Budget.objects.get(id=budget_id, user=request.user)
            budget.is_active = False
            budget.save()
            
            AuditLog.objects.create(
                user=request.user,
                action='BUDGET_DELETE',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={'budget_id': str(budget.id)}
            )
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Budget.DoesNotExist:
            return Response(
                {"error": "Budget not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class SavingsGoalListView(APIView):
    """List and create savings goals"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        goals = SavingsGoal.objects.filter(user=request.user, is_active=True)
        serializer = SavingsGoalSerializer(goals, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = SavingsGoalCreateSerializer(data=request.data)
        if serializer.is_valid():
            goal = serializer.save(user=request.user)
            
            AuditLog.objects.create(
                user=request.user,
                action='SAVINGS_GOAL_CREATE',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={'goal_id': str(goal.id), 'name': goal.name}
            )
            
            return Response(
                SavingsGoalSerializer(goal).data, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class SavingsGoalDetailView(APIView):
    """Get, update, and delete savings goals"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, goal_id):
        try:
            goal = SavingsGoal.objects.get(id=goal_id, user=request.user)
            serializer = SavingsGoalSerializer(goal)
            return Response(serializer.data)
        except SavingsGoal.DoesNotExist:
            return Response(
                {"error": "Savings goal not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def patch(self, request, goal_id):
        try:
            goal = SavingsGoal.objects.get(id=goal_id, user=request.user)
            serializer = SavingsGoalCreateSerializer(goal, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                
                AuditLog.objects.create(
                    user=request.user,
                    action='SAVINGS_GOAL_UPDATE',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                    payload={'goal_id': str(goal.id)}
                )
                
                return Response(SavingsGoalSerializer(goal).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except SavingsGoal.DoesNotExist:
            return Response(
                {"error": "Savings goal not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, goal_id):
        try:
            goal = SavingsGoal.objects.get(id=goal_id, user=request.user)
            goal.is_active = False
            goal.save()
            
            AuditLog.objects.create(
                user=request.user,
                action='SAVINGS_GOAL_DELETE',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={'goal_id': str(goal.id)}
            )
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except SavingsGoal.DoesNotExist:
            return Response(
                {"error": "Savings goal not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class DebtListView(APIView):
    """List and create debts"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        debts = Debt.objects.filter(user=request.user, is_active=True)
        serializer = DebtSerializer(debts, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = DebtCreateSerializer(data=request.data)
        if serializer.is_valid():
            debt = serializer.save(user=request.user)
            
            AuditLog.objects.create(
                user=request.user,
                action='DEBT_CREATE',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={'debt_id': str(debt.id), 'name': debt.name}
            )
            
            return Response(
                DebtSerializer(debt).data, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class DebtDetailView(APIView):
    """Get, update, and delete debts"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, debt_id):
        try:
            debt = Debt.objects.get(id=debt_id, user=request.user)
            serializer = DebtSerializer(debt)
            return Response(serializer.data)
        except Debt.DoesNotExist:
            return Response(
                {"error": "Debt not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def patch(self, request, debt_id):
        try:
            debt = Debt.objects.get(id=debt_id, user=request.user)
            serializer = DebtCreateSerializer(debt, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                
                AuditLog.objects.create(
                    user=request.user,
                    action='DEBT_UPDATE',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                    payload={'debt_id': str(debt.id)}
                )
                
                return Response(DebtSerializer(debt).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Debt.DoesNotExist:
            return Response(
                {"error": "Debt not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, debt_id):
        try:
            debt = Debt.objects.get(id=debt_id, user=request.user)
            debt.is_active = False
            debt.save()
            
            AuditLog.objects.create(
                user=request.user,
                action='DEBT_DELETE',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={'debt_id': str(debt.id)}
            )
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Debt.DoesNotExist:
            return Response(
                {"error": "Debt not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class BudgetSummaryView(APIView):
    """Get budget summary statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        month = request.query_params.get('month')
        
        # Default to current month
        if month:
            year, month_num = month.split('-')
            month_start = datetime(int(year), int(month_num), 1).date()
        else:
            month_start = timezone.now().date().replace(day=1)
        
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        budgets = Budget.objects.filter(user=request.user, is_active=True, month_start=month_start)
        
        total_budget = sum(b.limit_amount for b in budgets)
        total_spent = sum(b.spent_amount for b in budgets)
        total_remaining = total_budget - total_spent
        over_budget_count = sum(1 for b in budgets if b.spent_amount > b.limit_amount)
        
        # Category breakdown
        category_breakdown = {}
        for budget in budgets:
            category_breakdown[budget.category] = {
                'limit': str(budget.limit_amount),
                'spent': str(budget.spent_amount),
                'remaining': str(budget.remaining_amount),
                'percentage_used': str(budget.percentage_used)
            }
        
        summary_data = {
            'total_budget': total_budget,
            'total_spent': total_spent,
            'total_remaining': total_remaining,
            'budget_count': budgets.count(),
            'over_budget_count': over_budget_count,
            'category_breakdown': category_breakdown
        }
        
        serializer = BudgetSummarySerializer(summary_data)
        return Response(serializer.data)


class SavingsSummaryView(APIView):
    """Get savings summary statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        goals = SavingsGoal.objects.filter(user=request.user, is_active=True)
        
        total_target = sum(g.target_amount for g in goals)
        total_saved = sum(g.current_amount for g in goals)
        completed_goals = goals.filter(is_completed=True).count()
        
        goals_progress = []
        for goal in goals:
            goals_progress.append({
                'id': str(goal.id),
                'name': goal.name,
                'target': str(goal.target_amount),
                'current': str(goal.current_amount),
                'progress': str(goal.progress_percentage),
                'target_date': goal.target_date.isoformat()
            })
        
        summary_data = {
            'total_goals': goals.count(),
            'total_target': total_target,
            'total_saved': total_saved,
            'completed_goals': completed_goals,
            'goals_progress': goals_progress
        }
        
        serializer = SavingsSummarySerializer(summary_data)
        return Response(serializer.data)


class DebtSummaryView(APIView):
    """Get debt summary statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        debts = Debt.objects.filter(user=request.user, is_active=True)
        
        total_debt = sum(d.total_balance for d in debts)
        total_minimum_payments = sum(d.minimum_payment for d in debts)
        
        # Debt breakdown by type
        debt_breakdown = {}
        for debt in debts:
            if debt.type not in debt_breakdown:
                debt_breakdown[debt.type] = {
                    'count': 0,
                    'total_balance': Decimal('0.00'),
                    'total_minimum': Decimal('0.00')
                }
            debt_breakdown[debt.type]['count'] += 1
            debt_breakdown[debt.type]['total_balance'] += debt.total_balance
            debt_breakdown[debt.type]['total_minimum'] += debt.minimum_payment
        
        summary_data = {
            'total_debt': total_debt,
            'total_minimum_payments': total_minimum_payments,
            'debt_count': debts.count(),
            'debt_breakdown': debt_breakdown
        }
        
        serializer = DebtSummarySerializer(summary_data)
        return Response(serializer.data)