from rest_framework import viewsets, status, permissions
from rest_framework.permissions import BasePermission
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Avg, Q, Count, F, Case, When, Value, IntegerField
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
from .models import SpendingHeatmap, FinancialScore, ExpenseForecast, MonthlyReport, CategoryTrend
from .serializers import (
    SpendingHeatmapSerializer,
    FinancialScoreSerializer,
    ExpenseForecastSerializer,
    MonthlyReportSerializer,
    CategoryTrendSerializer,
    AnalyticsDashboardSerializer,
    SpendingPatternSerializer,
    BudgetHealthSerializer,
    YearOverYearComparisonSerializer
)


class IsAdminRole(BasePermission):
    """Allow access to staff users and users with the ADMIN role."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and (
                getattr(user, 'is_staff', False)
                or getattr(user, 'is_superuser', False)
                or getattr(user, 'role', '') == 'ADMIN'
            )
        )


class SpendingHeatmapViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing spending heatmap"""
    serializer_class = SpendingHeatmapSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's spending heatmap data"""
        queryset = SpendingHeatmap.objects.filter(user=self.request.user)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate spending heatmap data"""
        user = request.user
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse dates
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get transactions in date range
        from apps.ledger.models import Transaction
        transactions = Transaction.objects.filter(
            account__user=user,
            type='EXPENSE',
            timestamp__date__gte=start,
            timestamp__date__lte=end
        )
        
        # Group by date
        from django.db.models.functions import TruncDate
        daily_spending = transactions.annotate(
            date_only=TruncDate('timestamp')
        ).values('date_only').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('date_only')
        
        # Create or update heatmap records
        created_records = []
        for daily in daily_spending:
            heatmap, created = SpendingHeatmap.objects.get_or_create(
                user=user,
                date=daily['date_only'],
                defaults={
                    'total_spent': daily['total'],
                    'transaction_count': daily['count']
                }
            )
            
            if not created:
                heatmap.total_spent = daily['total']
                heatmap.transaction_count = daily['count']
                heatmap.save()
            
            created_records.append(heatmap)
        
        serializer = SpendingHeatmapSerializer(created_records, many=True)
        return Response(serializer.data)


class FinancialScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing financial scores"""
    serializer_class = FinancialScoreSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's financial scores"""
        return FinancialScore.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Calculate financial score"""
        user = request.user
        
        # Calculate scores for each dimension
        # Savings score (0-100)
        savings_score = self._calculate_savings_score(user)
        
        # Budgeting score (0-100)
        budgeting_score = self._calculate_budgeting_score(user)
        
        # Debt score (0-100)
        debt_score = self._calculate_debt_score(user)
        
        # Investment score (0-100)
        investment_score = self._calculate_investment_score(user)
        
        # Overall score (weighted average)
        overall_score = int(
            savings_score * 0.3 +
            budgeting_score * 0.3 +
            debt_score * 0.2 +
            investment_score * 0.2
        )
        
        # Generate insights
        insights = self._generate_insights(
            savings_score, budgeting_score, debt_score, investment_score
        )
        
        # Create financial score
        score = FinancialScore.objects.create(
            user=user,
            overall_score=overall_score,
            savings_score=savings_score,
            budgeting_score=budgeting_score,
            debt_score=debt_score,
            investment_score=investment_score,
            insights=insights
        )
        
        serializer = FinancialScoreSerializer(score)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _calculate_savings_score(self, user):
        """Calculate savings score"""
        from apps.budgeting.models import SavingsGoal
        
        # Get active savings goals
        goals = SavingsGoal.objects.filter(user=user, is_active=True)
        
        if not goals.exists():
            return 50  # Default score if no goals
        
        # Calculate average progress
        total_progress = sum(goal.progress_percentage for goal in goals)
        avg_progress = total_progress / len(goals)
        
        # Score based on progress
        return min(100, int(avg_progress))
    
    def _calculate_budgeting_score(self, user):
        """Calculate budgeting score"""
        from apps.budgeting.models import Budget
        
        # Get current month budgets
        current_month = date.today().replace(day=1)
        budgets = Budget.objects.filter(user=user, month_start=current_month, is_active=True)
        
        if not budgets.exists():
            return 50  # Default score if no budgets
        
        # Calculate how many budgets are on track
        on_track = sum(1 for budget in budgets if budget.percentage_used < 80)
        score = (on_track / len(budgets)) * 100
        
        return int(score)
    
    def _calculate_debt_score(self, user):
        """Calculate debt score"""
        from apps.budgeting.models import Debt
        
        # Get active debts
        debts = Debt.objects.filter(user=user, is_active=True)
        
        if not debts.exists():
            return 100  # Perfect score if no debt
        
        # Calculate total debt and minimum payments
        total_debt = sum(debt.total_balance for debt in debts)
        
        # Score based on debt-to-income ratio (simplified)
        # Lower debt = higher score
        if total_debt == 0:
            return 100
        
        # This is simplified - in reality, you'd need income data
        return max(0, 100 - int(total_debt / 1000))
    
    def _calculate_investment_score(self, user):
        """Calculate investment score"""
        from apps.investments.models import InvestmentAccount
        
        # Get investment accounts
        accounts = InvestmentAccount.objects.filter(user=user, is_active=True)
        
        if not accounts.exists():
            return 30  # Low score if no investments
        
        # Calculate diversification
        account_types = set(account.type for account in accounts)
        diversification_score = min(100, len(account_types) * 20)
        
        # Calculate performance
        total_profit_loss = sum(
            account.balance - self._get_total_invested(account)
            for account in accounts
        )
        
        performance_score = min(100, max(0, 50 + int(total_profit_loss / 100)))
        
        return int((diversification_score + performance_score) / 2)
    
    def _get_total_invested(self, account):
        """Get total amount invested in an account"""
        from apps.investments.models import Investment
        total = Investment.objects.filter(
            account=account,
            transaction_type='BUY'
        ).aggregate(total=Sum('total_amount'))['total']
        return total or Decimal('0')
    
    def _generate_insights(self, savings, budgeting, debt, investment):
        """Generate insights based on scores"""
        insights = []
        
        if savings < 60:
            insights.append("Consider increasing your savings rate")
        if budgeting < 60:
            insights.append("Review your budgets to stay on track")
        if debt < 60:
            insights.append("Focus on reducing high-interest debt")
        if investment < 60:
            insights.append("Start investing to build long-term wealth")
        
        if savings >= 80 and budgeting >= 80:
            insights.append("Great job managing your finances!")
        
        return insights


class ExpenseForecastViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing expense forecasts"""
    serializer_class = ExpenseForecastSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's expense forecasts"""
        return ExpenseForecast.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate expense forecast"""
        user = request.user
        forecast_date = request.data.get('forecast_date')
        
        if not forecast_date:
            return Response(
                {'error': 'forecast_date is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse date
        forecast_date = datetime.strptime(forecast_date, '%Y-%m-%d').date()
        
        # Get historical data (last 3 months)
        three_months_ago = forecast_date - timedelta(days=90)
        
        from apps.ledger.models import Transaction
        historical_transactions = Transaction.objects.filter(
            account__user=user,
            type='EXPENSE',
            timestamp__date__gte=three_months_ago,
            timestamp__date__lt=forecast_date
        )
        
        # Group by category
        from django.db.models.functions import TruncDate
        category_spending = historical_transactions.values('category').annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Calculate predictions
        category_breakdown = {}
        total_predicted = Decimal('0')
        
        for cat in category_spending:
            # Average daily spending for this category
            days = (forecast_date - three_months_ago).days
            daily_avg = cat['total'] / days
            
            # Predict for forecast date
            predicted = daily_avg
            category_breakdown[cat['category']] = {
                'predicted_amount': predicted,
                'confidence': 85.0  # Simplified confidence score
            }
            total_predicted += predicted
        
        # Create forecast
        forecast = ExpenseForecast.objects.create(
            user=user,
            forecast_date=forecast_date,
            predicted_amount=total_predicted,
            confidence_score=85.0,
            category_breakdown=category_breakdown,
            model_version='v1.0'
        )
        
        serializer = ExpenseForecastSerializer(forecast)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MonthlyReportViewSet(viewsets.ModelViewSet):
    """ViewSet for managing monthly reports"""
    serializer_class = MonthlyReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's reports"""
        return MonthlyReport.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create report for current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """Generate a new report"""
        report_type = request.data.get('report_type')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        file_format = request.data.get('file_format', 'CSV')
        
        if not report_type or not start_date or not end_date:
            return Response(
                {'error': 'report_type, start_date, and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse dates
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate report title
        title = f"{report_type.title()} Report ({start_date} to {end_date})"
        
        # Create report record
        report = MonthlyReport.objects.create(
            user=request.user,
            report_type=report_type,
            title=title,
            start_date=start,
            end_date=end,
            file_format=file_format.upper()
        )
        
        # Generate report data
        report_data = self.generate_report_data(request.user, report_type, start, end)
        report.data = report_data
        
        # Generate file based on format
        if file_format.upper() == 'CSV':
            file_path = self.generate_csv_report(request.user, report, start, end)
            report.file = file_path
        elif file_format.upper() == 'PDF':
            file_path = self.generate_pdf_report(request.user, report, start, end)
            report.file = file_path
        elif file_format.upper() == 'XLSX':
            file_path = self.generate_excel_report(request.user, report, start, end)
            report.file = file_path
        
        report.is_generated = True
        report.generated_at = timezone.now()
        report.save()
        
        serializer = MonthlyReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def generate_report_data(self, user, report_type, start_date, end_date):
        """Generate report data based on type"""
        from apps.ledger.models import Transaction
        from apps.budgeting.models import Budget, SavingsGoal, Debt
        from apps.bills.models import Bill
        
        # Get transactions
        transactions = Transaction.objects.filter(
            account__user=user,
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        )
        
        income = transactions.filter(type='INCOME').aggregate(total=Sum('amount'))['total'] or Decimal('0')
        expenses = transactions.filter(type='EXPENSE').aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Category breakdown
        category_breakdown = transactions.filter(type='EXPENSE').values('category').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        report_data = {
            'summary': {
                'total_income': float(income),
                'total_expenses': float(expenses),
                'net_savings': float(income - expenses),
                'savings_rate': float((income - expenses) / income * 100) if income > 0 else 0
            },
            'transactions': {
                'total_count': transactions.count(),
                'income_count': transactions.filter(type='INCOME').count(),
                'expense_count': transactions.filter(type='EXPENSE').count()
            },
            'category_breakdown': [
                {
                    'category': item['category'],
                    'total': float(item['total']),
                    'count': item['count'],
                    'percentage': float(item['total'] / expenses * 100) if expenses > 0 else 0
                }
                for item in category_breakdown
            ]
        }
        
        # Add type-specific data
        if report_type == 'BUDGET':
            budgets = Budget.objects.filter(user=user, is_active=True)
            report_data['budgets'] = [
                {
                    'category': b.category,
                    'limit': float(b.limit_amount),
                    'spent': float(b.spent_amount),
                    'remaining': float(b.limit_amount - b.spent_amount),
                    'percentage_used': float(b.percentage_used)
                }
                for b in budgets
            ]
        
        elif report_type == 'INVESTMENT':
            from apps.investments.models import InvestmentAccount, Investment
            accounts = InvestmentAccount.objects.filter(user=user, is_active=True)
            report_data['investments'] = [
                {
                    'name': acc.name,
                    'type': acc.type,
                    'balance': float(acc.balance),
                    'total_invested': float(self.get_total_invested(acc))
                }
                for acc in accounts
            ]
        
        elif report_type == 'TAX':
            # Tax-related transactions
            tax_deductible = transactions.filter(
                type='EXPENSE',
                category__in=['Healthcare', 'Charity', 'Education', 'Business']
            )
            report_data['tax_summary'] = {
                'total_tax_deductible': float(tax_deductible.aggregate(total=Sum('amount'))['total'] or 0),
                'deductible_categories': list(tax_deductible.values('category').annotate(
                    total=Sum('amount')
                ).order_by('-total'))
            }
        
        return report_data
    
    def get_total_invested(self, account):
        """Get total amount invested in an account"""
        from apps.investments.models import Investment
        total = Investment.objects.filter(
            account=account,
            transaction_type='BUY'
        ).aggregate(total=Sum('total_amount'))['total']
        return total or Decimal('0')
    
    def generate_csv_report(self, user, report, start_date, end_date):
        """Generate CSV report"""
        import csv
        import os
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        
        from apps.ledger.models import Transaction
        
        transactions = Transaction.objects.filter(
            account__user=user,
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        ).order_by('-timestamp')
        
        # Create CSV content
        csv_content = "Date,Title,Category,Type,Amount,Note,Tags\n"
        for tx in transactions:
            csv_content += f"{tx.timestamp.strftime('%Y-%m-%d')},\"{tx.title}\",\"{tx.category}\",{tx.type},{tx.amount},\"{tx.note}\",\"{tx.tags}\"\n"
        
        # Save file
        filename = f"reports/{user.id}/{report.id}.csv"
        path = default_storage.save(filename, ContentFile(csv_content.encode('utf-8')))
        
        return path
    
    def generate_excel_report(self, user, report, start_date, end_date):
        """Generate Excel report"""
        # For now, return CSV path (in production, use openpyxl or xlsxwriter)
        return self.generate_csv_report(user, report, start_date, end_date)
    
    def generate_pdf_report(self, user, report, start_date, end_date):
        """Generate PDF report"""
        # For now, return CSV path (in production, use reportlab or weasyprint)
        return self.generate_csv_report(user, report, start_date, end_date)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download report file"""
        report = self.get_object()
        
        if not report.file:
            return Response(
                {'error': 'Report file not generated yet'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from django.http import FileResponse
        import os
        
        file_path = report.file.path
        if os.path.exists(file_path):
            response = FileResponse(
                open(file_path, 'rb'),
                as_attachment=True,
                filename=f"{report.title}.{report.file_format.lower()}"
            )
            return response
        else:
            return Response(
                {'error': 'File not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class CategoryTrendViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing category trends"""
    serializer_class = CategoryTrendSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's category trends"""
        queryset = CategoryTrend.objects.filter(user=self.request.user)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by period
        period = self.request.query_params.get('period')
        if period:
            queryset = queryset.filter(period=period)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate category trends"""
        user = request.user
        period = request.data.get('period')  # e.g., '2024-01', '2024-Q1'
        
        if not period:
            return Response(
                {'error': 'period is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse period
        if '-' in period and len(period) == 7:  # Monthly: '2024-01'
            year, month = period.split('-')
            year = int(year)
            month = int(month)
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
        else:  # Quarterly or other
            return Response(
                {'error': 'Invalid period format. Use YYYY-MM'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get transactions in period
        from apps.ledger.models import Transaction
        transactions = Transaction.objects.filter(
            account__user=user,
            type='EXPENSE',
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        )
        
        # Group by category
        category_data = transactions.values('category').annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Calculate total spending
        total_spending = sum(cat['total'] for cat in category_data)
        
        # Get previous period for comparison
        if month == 1:
            prev_year = year - 1
            prev_month = 12
        else:
            prev_year = year
            prev_month = month - 1
        
        prev_period = f"{prev_year}-{prev_month:02d}"
        prev_trends = CategoryTrend.objects.filter(
            user=user,
            period=prev_period
        )
        
        prev_trends_dict = {trend.category: trend for trend in prev_trends}
        
        # Create trends
        created_trends = []
        for cat in category_data:
            category = cat['category']
            amount = cat['total']
            count = cat['count']
            
            # Calculate percentage of total
            percentage = (amount / total_spending * 100) if total_spending > 0 else 0
            
            # Calculate change from previous period
            if category in prev_trends_dict:
                prev_amount = prev_trends_dict[category].amount
                change = ((amount - prev_amount) / prev_amount * 100) if prev_amount > 0 else 0
            else:
                change = 0
            
            # Create or update trend
            trend, created = CategoryTrend.objects.get_or_create(
                user=user,
                category=category,
                period=period,
                defaults={
                    'amount': amount,
                    'transaction_count': count,
                    'percentage_of_total': percentage,
                    'change_from_previous': change
                }
            )
            
            if not created:
                trend.amount = amount
                trend.transaction_count = count
                trend.percentage_of_total = percentage
                trend.change_from_previous = change
                trend.save()
            
            created_trends.append(trend)
        
        serializer = CategoryTrendSerializer(created_trends, many=True)
        return Response(serializer.data)


class AnalyticsDashboardViewSet(viewsets.ViewSet):
    """ViewSet for analytics dashboard"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get analytics dashboard data"""
        user = request.user
        
        # Get current and last month
        today = date.today()
        current_month_start = today.replace(day=1)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        # Calculate spending for current and last month
        from apps.ledger.models import Transaction
        
        current_month_spending = Transaction.objects.filter(
            account__user=user,
            type='EXPENSE',
            timestamp__date__gte=current_month_start,
            timestamp__date__lte=today
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        last_month_spending = Transaction.objects.filter(
            account__user=user,
            type='EXPENSE',
            timestamp__date__gte=last_month_start,
            timestamp__date__lt=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Calculate month-over-month change
        if last_month_spending > 0:
            mom_change = ((current_month_spending - last_month_spending) / last_month_spending) * 100
        else:
            mom_change = 0
        
        # Get top categories
        top_categories = CategoryTrend.objects.filter(
            user=user,
            period=current_month_start.strftime('%Y-%m')
        ).order_by('-amount')[:5]
        top_categories_serializer = CategoryTrendSerializer(top_categories, many=True)
        
        # Get recent heatmap (last 7 days)
        seven_days_ago = today - timedelta(days=7)
        recent_heatmap = SpendingHeatmap.objects.filter(
            user=user,
            date__gte=seven_days_ago
        ).order_by('-date')
        heatmap_serializer = SpendingHeatmapSerializer(recent_heatmap, many=True)
        
        # Get latest financial score
        latest_score = FinancialScore.objects.filter(user=user).first()
        score_serializer = FinancialScoreSerializer(latest_score) if latest_score else None
        
        # Get latest forecast
        latest_forecast = ExpenseForecast.objects.filter(
            user=user,
            forecast_date__gte=today
        ).first()
        forecast_serializer = ExpenseForecastSerializer(latest_forecast) if latest_forecast else None
        
        # Get category trends
        category_trends = CategoryTrend.objects.filter(
            user=user,
            period=current_month_start.strftime('%Y-%m')
        ).order_by('-amount')
        trends_serializer = CategoryTrendSerializer(category_trends, many=True)
        
        # Get budget health
        budget_health = self.get_budget_health(user)
        
        # Get year-over-year comparison
        yoy_comparison = self.get_year_over_year_comparison(user)
        
        data = {
            'total_spent_this_month': current_month_spending,
            'total_spent_last_month': last_month_spending,
            'month_over_month_change': mom_change,
            'top_categories': top_categories_serializer.data,
            'recent_heatmap': heatmap_serializer.data,
            'financial_score': score_serializer.data if score_serializer else None,
            'forecast': forecast_serializer.data if forecast_serializer else None,
            'category_trends': trends_serializer.data,
            'budget_health': budget_health,
            'year_over_year': yoy_comparison
        }
        
        serializer = AnalyticsDashboardSerializer(data)
        return Response(serializer.data)
    
    def get_budget_health(self, user):
        """Calculate budget health metrics"""
        from apps.budgeting.models import Budget
        
        budgets = Budget.objects.filter(user=user, is_active=True)
        
        if not budgets.exists():
            return {
                'total_budgets': 0,
                'on_track_budgets': 0,
                'at_risk_budgets': 0,
                'over_budget': 0,
                'health_percentage': 0,
                'recommendations': ['Create budgets to track your spending']
            }
        
        total_budgets = budgets.count()
        on_track = 0
        at_risk = 0
        over_budget = 0
        recommendations = []
        
        for budget in budgets:
            percentage_used = budget.percentage_used
            
            if percentage_used >= 100:
                over_budget += 1
                recommendations.append(f"⚠️ {budget.category} is over budget by ${budget.spent_amount - budget.limit_amount:.2f}")
            elif percentage_used >= 80:
                at_risk += 1
                recommendations.append(f"⚡ {budget.category} is at {percentage_used:.0f}% of budget")
            else:
                on_track += 1
        
        health_percentage = (on_track / total_budgets * 100) if total_budgets > 0 else 0
        
        return {
            'total_budgets': total_budgets,
            'on_track_budgets': on_track,
            'at_risk_budgets': at_risk,
            'over_budget': over_budget,
            'health_percentage': round(health_percentage, 2),
            'recommendations': recommendations[:5]  # Top 5 recommendations
        }
    
    def get_year_over_year_comparison(self, user):
        """Calculate year-over-year spending comparison"""
        from apps.ledger.models import Transaction
        
        today = date.today()
        current_year = today.year
        last_year = current_year - 1
        
        # Current year spending
        current_year_start = date(current_year, 1, 1)
        current_year_spending = Transaction.objects.filter(
            account__user=user,
            type='EXPENSE',
            timestamp__date__gte=current_year_start,
            timestamp__date__lte=today
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Last year spending
        last_year_start = date(last_year, 1, 1)
        last_year_end = date(last_year, 12, 31)
        last_year_spending = Transaction.objects.filter(
            account__user=user,
            type='EXPENSE',
            timestamp__date__gte=last_year_start,
            timestamp__date__lte=last_year_end
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Calculate change
        if last_year_spending > 0:
            change_amount = current_year_spending - last_year_spending
            change_percentage = (change_amount / last_year_spending) * 100
        else:
            change_amount = current_year_spending
            change_percentage = 0
        
        # By category
        current_year_by_category = Transaction.objects.filter(
            account__user=user,
            type='EXPENSE',
            timestamp__date__gte=current_year_start,
            timestamp__date__lte=today
        ).values('category').annotate(total=Sum('amount')).order_by('-total')
        
        by_category = {item['category']: float(item['total']) for item in current_year_by_category}
        
        # By month (current year)
        by_month = {}
        for month in range(1, today.month + 1):
            month_start = date(current_year, month, 1)
            if month == 12:
                month_end = date(current_year, 12, 31)
            else:
                month_end = date(current_year, month + 1, 1) - timedelta(days=1)
            
            month_spending = Transaction.objects.filter(
                account__user=user,
                type='EXPENSE',
                timestamp__date__gte=month_start,
                timestamp__date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            by_month[f"{current_year}-{month:02d}"] = float(month_spending)
        
        return {
            'current_year_total': float(current_year_spending),
            'previous_year_total': float(last_year_spending),
            'change_amount': float(change_amount),
            'change_percentage': round(float(change_percentage), 2),
            'by_category': by_category,
            'by_month': by_month
        }


class AdminDashboardViewSet(viewsets.ViewSet):
    """Admin-only operational dashboard endpoints."""

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    @action(detail=False, methods=['get'])
    def summary(self, request):
        from apps.authentication.models import User, AuditLog, LoginHistory
        from apps.payments.models import UserSubscription, Payment, Invoice
        from apps.ai_copilot.models import AIUsageLog

        total_users = User.objects.count()
        active_users_30d = LoginHistory.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30),
            status='SUCCESS'
        ).values('user_id').distinct().count()
        active_subscriptions = UserSubscription.objects.filter(is_active=True).count()
        successful_payments = Payment.objects.filter(status='SUCCEEDED').count()
        revenue_cents = Payment.objects.filter(status='SUCCEEDED').aggregate(total=Sum('amount_cents'))['total'] or 0
        pending_invoices = Invoice.objects.filter(status__in=['open', 'draft', 'unpaid']).count()
        api_calls = AIUsageLog.objects.count()
        failed_api_calls = AIUsageLog.objects.filter(success=False).count()

        return Response({
            'total_users': total_users,
            'active_users_30d': active_users_30d,
            'active_subscriptions': active_subscriptions,
            'successful_payments': successful_payments,
            'revenue': {
                'cents': revenue_cents,
                'dollars': round(revenue_cents / 100, 2),
            },
            'pending_invoices': pending_invoices,
            'api_calls': api_calls,
            'failed_api_calls': failed_api_calls,
            'audit_events_30d': AuditLog.objects.filter(created_at__gte=timezone.now() - timedelta(days=30)).count(),
        })

    @action(detail=False, methods=['get'])
    def users(self, request):
        from apps.authentication.models import User, LoginHistory
        from apps.authentication.serializers import UserSerializer

        role_counts = {
            'USER': User.objects.filter(role='USER').count(),
            'ADMIN': User.objects.filter(role='ADMIN').count(),
            'SUPPORT': User.objects.filter(role='SUPPORT').count(),
        }
        recent_users = User.objects.order_by('-created_at')[:25]
        recent_serializer = UserSerializer(recent_users, many=True)
        recent_logins = LoginHistory.objects.order_by('-created_at')[:25]

        return Response({
            'role_counts': role_counts,
            'total_users': User.objects.count(),
            'recent_users': recent_serializer.data,
            'recent_logins': [
                {
                    'user_id': str(item.user_id),
                    'status': item.status,
                    'created_at': item.created_at,
                    'ip_address': item.ip_address,
                }
                for item in recent_logins
            ],
        })

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        from apps.payments.models import SubscriptionPlan, UserSubscription, Payment, Invoice

        active_subscriptions = UserSubscription.objects.filter(is_active=True)
        monthly_mrr_cents = 0
        for subscription in active_subscriptions.select_related('plan'):
            monthly_mrr_cents += subscription.plan.price_cents

        payment_totals = Payment.objects.filter(status='SUCCEEDED').aggregate(total=Sum('amount_cents'))['total'] or 0
        invoice_totals = Invoice.objects.aggregate(total=Sum('amount_cents'))['total'] or 0

        return Response({
            'subscription_plans': SubscriptionPlan.objects.filter(is_active=True).count(),
            'active_subscriptions': active_subscriptions.count(),
            'mrr': {
                'cents': monthly_mrr_cents,
                'dollars': round(monthly_mrr_cents / 100, 2),
            },
            'payment_volume': {
                'cents': payment_totals,
                'dollars': round(payment_totals / 100, 2),
            },
            'invoice_volume': {
                'cents': invoice_totals,
                'dollars': round(invoice_totals / 100, 2),
            },
            'active_by_status': {
                'ACTIVE': active_subscriptions.filter(status='ACTIVE').count(),
                'PAST_DUE': active_subscriptions.filter(status='PAST_DUE').count(),
                'CANCELED': UserSubscription.objects.filter(status='CANCELED').count(),
            },
        })

    @action(detail=False, methods=['get'])
    def logs(self, request):
        from apps.authentication.models import AuditLog, LoginHistory
        from apps.authentication.serializers import AuditLogSerializer

        audit_logs = AuditLog.objects.order_by('-created_at')[:50]
        login_history = LoginHistory.objects.order_by('-created_at')[:50]

        return Response({
            'audit_logs': AuditLogSerializer(audit_logs, many=True).data,
            'login_history': [
                {
                    'id': str(item.id),
                    'user_id': str(item.user_id),
                    'login_time': item.login_time,
                    'logout_time': item.logout_time,
                    'ip_address': item.ip_address,
                    'device_info': item.device_info,
                }
                for item in login_history
            ],
            'failed_logins_30d': LoginHistory.objects.filter(
                status='FAILED',
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'two_factor_required_30d': LoginHistory.objects.filter(
                status='2FA_REQUIRED',
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count(),
        })

    @action(detail=False, methods=['get'])
    def monitoring(self, request):
        from apps.ai_copilot.models import AIUsageLog

        recent_usage_qs = AIUsageLog.objects.order_by('-created_at')
        recent_usage = recent_usage_qs[:100]
        successful = recent_usage_qs.filter(success=True).count()
        failed = recent_usage_qs.filter(success=False).count()
        avg_response = recent_usage_qs.aggregate(avg=Avg('response_time_ms'))['avg'] or 0

        queue_status = {
            'available': False,
            'workers': 0,
            'active_tasks': 0,
            'reserved_tasks': 0,
        }

        try:
            from celery import current_app

            inspector = current_app.control.inspect(timeout=1)
            active = inspector.active() or {}
            reserved = inspector.reserved() or {}
            queue_status = {
                'available': True,
                'workers': len(active.keys()),
                'active_tasks': sum(len(tasks or []) for tasks in active.values()),
                'reserved_tasks': sum(len(tasks or []) for tasks in reserved.values()),
            }
        except Exception:
            pass

        return Response({
            'api_usage': {
                'recent_calls': recent_usage.count(),
                'successful_calls': successful,
                'failed_calls': failed,
                'avg_response_time_ms': round(avg_response, 2),
            },
            'queue': queue_status,
        })


class SyncViewSet(viewsets.ViewSet):
    """Delta sync endpoints for offline-first clients."""

    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def delta(self, request):
        from apps.ledger.models import Account, Transaction, Category, Attachment
        from apps.ledger.serializers import AccountSerializer, TransactionSerializer, CategorySerializer, AttachmentSerializer
        from apps.budgeting.models import Budget, SavingsGoal, Debt
        from apps.budgeting.serializers import BudgetSerializer, SavingsGoalSerializer, DebtSerializer
        from apps.bills.models import Bill, BillPayment
        from apps.bills.serializers import BillSerializer, BillPaymentSerializer
        from apps.documents.models import Document
        from apps.documents.serializers import DocumentSerializer
        from apps.receipts.models import ReceiptScan
        from apps.receipts.serializers import ReceiptScanSerializer
        from apps.investments.models import InvestmentAccount, Investment, PortfolioAllocation, InvestmentPerformance
        from apps.investments.serializers import (
            InvestmentAccountSerializer,
            InvestmentSerializer,
            PortfolioAllocationSerializer,
            InvestmentPerformanceSerializer,
        )
        from apps.financial_calendar.models import FinancialCalendarEvent
        from apps.financial_calendar.serializers import FinancialCalendarEventSerializer

        since_param = request.query_params.get('since')
        if since_param:
            since = datetime.fromisoformat(since_param.replace('Z', '+00:00'))
            if timezone.is_naive(since):
                since = timezone.make_aware(since, timezone.get_current_timezone())
        else:
            since = timezone.now() - timedelta(days=1)

        def serialize(queryset, serializer_class):
            return serializer_class(queryset, many=True, context={'request': request}).data

        account_qs = Account.objects.filter(user=request.user).filter(updated_at__gte=since)
        transaction_qs = Transaction.objects.filter(account__user=request.user).filter(updated_at__gte=since)
        category_qs = Category.objects.filter(user=request.user).filter(created_at__gte=since)
        attachment_qs = Attachment.objects.filter(transaction__account__user=request.user).filter(uploaded_at__gte=since)
        budget_qs = Budget.objects.filter(user=request.user).filter(updated_at__gte=since)
        goal_qs = SavingsGoal.objects.filter(user=request.user).filter(updated_at__gte=since)
        debt_qs = Debt.objects.filter(user=request.user).filter(updated_at__gte=since)
        bill_qs = Bill.objects.filter(user=request.user).filter(updated_at__gte=since)
        bill_payment_qs = BillPayment.objects.filter(bill__user=request.user).filter(created_at__gte=since)
        document_qs = Document.objects.filter(user=request.user).filter(updated_at__gte=since)
        receipt_qs = ReceiptScan.objects.filter(user=request.user).filter(uploaded_at__gte=since)
        investment_account_qs = InvestmentAccount.objects.filter(user=request.user).filter(updated_at__gte=since)
        investment_qs = Investment.objects.filter(account__user=request.user).filter(created_at__gte=since)
        allocation_qs = PortfolioAllocation.objects.filter(user=request.user).filter(calculated_at__gte=since)
        performance_qs = InvestmentPerformance.objects.filter(account__user=request.user).filter(created_at__gte=since)
        calendar_qs = FinancialCalendarEvent.objects.filter(user=request.user).filter(updated_at__gte=since)

        return Response({
            'since': since.isoformat(),
            'server_time': timezone.now().isoformat(),
            'changes': {
                'accounts': serialize(account_qs, AccountSerializer),
                'transactions': serialize(transaction_qs, TransactionSerializer),
                'categories': serialize(category_qs, CategorySerializer),
                'attachments': serialize(attachment_qs, AttachmentSerializer),
                'budgets': serialize(budget_qs, BudgetSerializer),
                'goals': serialize(goal_qs, SavingsGoalSerializer),
                'debts': serialize(debt_qs, DebtSerializer),
                'bills': serialize(bill_qs, BillSerializer),
                'bill_payments': serialize(bill_payment_qs, BillPaymentSerializer),
                'documents': serialize(document_qs, DocumentSerializer),
                'receipts': serialize(receipt_qs, ReceiptScanSerializer),
                'investment_accounts': serialize(investment_account_qs, InvestmentAccountSerializer),
                'investments': serialize(investment_qs, InvestmentSerializer),
                'allocations': serialize(allocation_qs, PortfolioAllocationSerializer),
                'performance': serialize(performance_qs, InvestmentPerformanceSerializer),
                'calendar_events': serialize(calendar_qs, FinancialCalendarEventSerializer),
            },
        })


class NotificationCenterViewSet(viewsets.ViewSet):
    """Smart notification triggers and user notification preferences."""

    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def alerts(self, request):
        from apps.authentication.models import UserPreferences
        from apps.authentication.serializers import UserPreferencesSerializer
        from apps.bills.models import Bill
        from apps.budgeting.models import Budget, SavingsGoal
        from apps.ai_copilot.models import AIInsight

        today = timezone.now().date()
        upcoming_window = today + timedelta(days=7)

        upcoming_bills = Bill.objects.filter(
            user=request.user,
            is_active=True,
            is_paid=False,
            due_date__gte=today,
            due_date__lte=upcoming_window,
        ).order_by('due_date')

        budget_alerts = []
        for budget in Budget.objects.filter(user=request.user, is_active=True):
            if budget.percentage_used >= 80:
                budget_alerts.append({
                    'type': 'BUDGET_WARNING',
                    'title': f'{budget.category} budget is at {budget.percentage_used:.0f}%',
                    'description': f'Spent {budget.percentage_used:.0f}% of your {budget.category} budget.',
                    'priority': 2 if budget.percentage_used >= 100 else 1,
                })

        goal_alerts = []
        for goal in SavingsGoal.objects.filter(user=request.user, is_active=True):
            progress = goal.progress_percentage
            if progress >= 80 and not goal.is_completed:
                goal_alerts.append({
                    'type': 'GOAL_MILESTONE',
                    'title': f'{goal.name} is {progress:.0f}% complete',
                    'description': f'You are close to reaching your {goal.name} target.',
                    'priority': 1,
                })

        insights = AIInsight.objects.filter(
            user=request.user,
            is_read=False,
            is_dismissed=False,
        ).order_by('-priority', '-created_at')[:20]

        preferences, _ = UserPreferences.objects.get_or_create(user=request.user)

        alerts = []
        for bill in upcoming_bills:
            alerts.append({
                'type': 'BILL_REMINDER',
                'title': bill.name,
                'description': f'Due on {bill.due_date.isoformat()} for ${bill.amount}',
                'priority': 3,
                'due_date': bill.due_date,
            })
        alerts.extend(budget_alerts)
        alerts.extend(goal_alerts)
        alerts.extend([
            {
                'type': insight.insight_type,
                'title': insight.title,
                'description': insight.description,
                'priority': insight.priority,
            }
            for insight in insights
        ])

        return Response({
            'preferences': UserPreferencesSerializer(preferences).data,
            'alerts': sorted(alerts, key=lambda item: item.get('priority', 0), reverse=True),
            'counts': {
                'upcoming_bills': upcoming_bills.count(),
                'budget_alerts': len(budget_alerts),
                'goal_alerts': len(goal_alerts),
                'unread_insights': insights.count(),
            },
        })

    @action(detail=False, methods=['get'])
    def preferences(self, request):
        from apps.authentication.models import UserPreferences
        from apps.authentication.serializers import UserPreferencesSerializer

        preferences, _ = UserPreferences.objects.get_or_create(user=request.user)
        return Response(UserPreferencesSerializer(preferences).data)
