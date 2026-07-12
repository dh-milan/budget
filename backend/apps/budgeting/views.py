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


class BudgetRecommendationsView(APIView):
    """Generate budget recommendations based on spending patterns"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get current month's spending
        today = timezone.now()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get user's budgets
        budgets = Budget.objects.filter(user=request.user, is_active=True, month_start=month_start)
        
        # Get actual spending by category for current month
        from apps.ledger.models import Transaction
        transactions = Transaction.objects.filter(
            account__user=request.user,
            timestamp__gte=month_start,
            type='EXPENSE'
        )
        
        actual_spending = {}
        for tx in transactions:
            cat = tx.category
            actual_spending[cat] = actual_spending.get(cat, Decimal('0.00')) + tx.amount
        
        # Get historical spending (last 3 months)
        three_months_ago = month_start - timedelta(days=90)
        historical_transactions = Transaction.objects.filter(
            account__user=request.user,
            timestamp__gte=three_months_ago,
            timestamp__lt=month_start,
            type='EXPENSE'
        )
        
        historical_spending = {}
        for tx in historical_transactions:
            cat = tx.category
            historical_spending[cat] = historical_spending.get(cat, Decimal('0.00')) + tx.amount
        
        # Generate recommendations
        recommendations = []
        
        # 1. Categories where user is overspending
        for budget in budgets:
            category = budget.category
            spent = actual_spending.get(category, Decimal('0.00'))
            budget_limit = budget.limit_amount
            
            if spent > budget_limit:
                overspend_amount = spent - budget_limit
                overspend_percent = (overspend_amount / budget_limit * 100) if budget_limit > 0 else 0
                
                recommendations.append({
                    'type': 'OVERSPEND_ALERT',
                    'category': category,
                    'severity': 'HIGH' if overspend_percent > 50 else 'MEDIUM',
                    'message': f"You've overspent on {category} by ${overspend_amount:.2f} ({overspend_percent:.1f}% over budget)",
                    'current_spent': str(spent),
                    'budget_limit': str(budget_limit),
                    'suggested_action': f"Consider reducing {category} spending by ${overspend_amount:.2f} this month"
                })
        
        # 2. Categories without budgets but with significant spending
        for category, spent in actual_spending.items():
            if category not in [b.category for b in budgets] and spent > 100:
                recommendations.append({
                    'type': 'NO_BUDGET_WARNING',
                    'category': category,
                    'severity': 'MEDIUM',
                    'message': f"You've spent ${spent:.2f} on {category} without a budget",
                    'current_spent': str(spent),
                    'suggested_action': f"Consider setting a monthly budget of ${spent * Decimal('0.8'):.2f} for {category}"
                })
        
        # 3. Savings opportunities based on historical data
        for category, historical_avg in historical_spending.items():
            current_spent = actual_spending.get(category, Decimal('0.00'))
            monthly_avg = historical_avg / 3  # Average over 3 months
            
            if current_spent > monthly_avg * Decimal('1.2'):  # 20% over average
                excess = current_spent - monthly_avg
                recommendations.append({
                    'type': 'SAVINGS_OPPORTUNITY',
                    'category': category,
                    'severity': 'LOW',
                    'message': f"You're spending ${excess:.2f} more than usual on {category}",
                    'current_spent': str(current_spent),
                    'historical_average': str(monthly_avg),
                    'suggested_action': f"Reducing to your usual ${monthly_avg:.2f} could save ${excess:.2f}"
                })
        
        # 4. General recommendations
        total_spent = sum(actual_spending.values())
        if total_spent > 0:
            # Find top spending category
            top_category = max(actual_spending, key=actual_spending.get)
            top_amount = actual_spending[top_category]
            top_percent = (top_amount / total_spent * 100)
            
            if top_percent > 40:
                recommendations.append({
                    'type': 'CATEGORY_CONCENTRATION',
                    'category': top_category,
                    'severity': 'INFO',
                    'message': f"{top_category} represents {top_percent:.1f}% of your spending",
                    'current_spent': str(top_amount),
                    'suggested_action': f"Review if this aligns with your financial priorities"
                })
        
        # Sort by severity
        severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2, 'INFO': 3}
        recommendations.sort(key=lambda x: severity_order.get(x['severity'], 4))
        
        return Response({
            'recommendation_count': len(recommendations),
            'recommendations': recommendations,
            'month': month_start.strftime('%Y-%m')
        })


class BudgetVsActualView(APIView):
    """Get detailed budget vs actual spending comparison"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        month = request.query_params.get('month')
        
        if month:
            year, month_num = month.split('-')
            month_start = datetime(int(year), int(month_num), 1).date()
        else:
            month_start = timezone.now().date().replace(day=1)
        
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Get budgets
        budgets = Budget.objects.filter(user=request.user, is_active=True, month_start=month_start)
        
        # Get actual spending
        from apps.ledger.models import Transaction
        transactions = Transaction.objects.filter(
            account__user=request.user,
            timestamp__date__gte=month_start,
            timestamp__date__lte=month_end,
            type='EXPENSE'
        )
        
        actual_by_category = {}
        for tx in transactions:
            cat = tx.category
            actual_by_category[cat] = actual_by_category.get(cat, Decimal('0.00')) + tx.amount
        
        # Build comparison
        comparison = []
        for budget in budgets:
            category = budget.category
            actual = actual_by_category.get(category, Decimal('0.00'))
            variance = budget.limit_amount - actual
            variance_percent = (variance / budget.limit_amount * 100) if budget.limit_amount > 0 else 0
            
            comparison.append({
                'category': category,
                'budget': str(budget.limit_amount),
                'actual': str(actual),
                'variance': str(variance),
                'variance_percent': str(variance_percent),
                'status': 'OVER' if actual > budget.limit_amount else 'UNDER' if variance > 0 else 'EXACT'
            })
        
        # Add categories with spending but no budget
        for category, actual in actual_by_category.items():
            if category not in [b.category for b in budgets]:
                comparison.append({
                    'category': category,
                    'budget': '0.00',
                    'actual': str(actual),
                    'variance': str(-actual),
                    'variance_percent': '-100',
                    'status': 'NO_BUDGET'
                })
        
        return Response({
            'month': month_start.strftime('%Y-%m'),
            'comparison': comparison,
            'total_budget': str(sum(b.limit_amount for b in budgets)),
            'total_actual': str(sum(actual_by_category.values())),
            'categories_tracked': len(comparison)
        })
