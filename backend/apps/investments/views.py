from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from .models import InvestmentAccount, Investment, PortfolioAllocation, InvestmentPerformance
from .serializers import (
    InvestmentAccountSerializer,
    InvestmentSerializer,
    PortfolioAllocationSerializer,
    InvestmentPerformanceSerializer,
    PortfolioSummarySerializer,
    InvestmentInsightSerializer
)


class InvestmentAccountViewSet(viewsets.ModelViewSet):
    """ViewSet for managing investment accounts"""
    serializer_class = InvestmentAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's investment accounts"""
        return InvestmentAccount.objects.filter(user=self.request.user, is_active=True)
    
    def perform_create(self, serializer):
        """Create investment account for current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def investments(self, request, pk=None):
        """Get all investments for an account"""
        account = self.get_object()
        investments = account.investments.all()
        
        # Filter by date range if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            investments = investments.filter(transaction_date__gte=start_date)
        if end_date:
            investments = investments.filter(transaction_date__lte=end_date)
        
        serializer = InvestmentSerializer(investments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get performance history for an account"""
        account = self.get_object()
        days = int(request.query_params.get('days', 30))
        
        start_date = timezone.now() - timedelta(days=days)
        performance = account.performance_records.filter(date__gte=start_date)
        
        serializer = InvestmentPerformanceSerializer(performance, many=True)
        return Response(serializer.data)


class InvestmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing individual investments"""
    serializer_class = InvestmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's investments"""
        user = self.request.user
        return Investment.objects.filter(account__user=user).select_related('account')
    
    def perform_create(self, serializer):
        """Create investment and update account balance"""
        investment = serializer.save()
        
        # Update account balance based on transaction type
        account = investment.account
        if investment.transaction_type == 'BUY':
            account.balance += investment.total_amount
        elif investment.transaction_type == 'SELL':
            account.balance -= investment.total_amount
        elif investment.transaction_type == 'DIVIDEND':
            account.balance += investment.total_amount
        
        account.save()
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get investment summary"""
        user = request.user
        accounts = InvestmentAccount.objects.filter(user=user, is_active=True)
        
        total_value = sum(account.balance for account in accounts)
        
        # Calculate total invested
        total_invested = Investment.objects.filter(
            account__user=user,
            transaction_type='BUY'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        # Calculate total profit/loss
        total_profit_loss = total_value - total_invested
        total_profit_loss_percentage = (
            (total_profit_loss / total_invested * 100) 
            if total_invested > 0 else Decimal('0')
        )
        
        # Get portfolio allocation
        allocation = PortfolioAllocation.objects.filter(user=user)
        allocation_serializer = PortfolioAllocationSerializer(allocation, many=True)
        
        # Get recent performance
        recent_performance = InvestmentPerformance.objects.filter(
            account__user=user
        ).order_by('-date')[:30]
        performance_serializer = InvestmentPerformanceSerializer(recent_performance, many=True)
        
        # Serialize accounts
        account_serializer = InvestmentAccountSerializer(accounts, many=True)
        
        data = {
            'total_value': total_value,
            'total_invested': total_invested,
            'total_profit_loss': total_profit_loss,
            'total_profit_loss_percentage': total_profit_loss_percentage,
            'accounts': account_serializer.data,
            'allocation': allocation_serializer.data,
            'recent_performance': performance_serializer.data
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def by_symbol(self, request):
        """Get investments grouped by symbol"""
        user = request.user
        symbol = request.query_params.get('symbol')
        
        investments = Investment.objects.filter(account__user=user)
        
        if symbol:
            investments = investments.filter(symbol=symbol)
        
        investments = investments.order_by('symbol', '-transaction_date')
        serializer = InvestmentSerializer(investments, many=True)
        return Response(serializer.data)


class PortfolioAllocationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing portfolio allocation"""
    serializer_class = PortfolioAllocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's portfolio allocations"""
        return PortfolioAllocation.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create allocation for current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def recalculate(self, request):
        """Recalculate portfolio allocation based on current investments"""
        user = request.user
        accounts = InvestmentAccount.objects.filter(user=user, is_active=True)
        
        # Clear existing allocations
        PortfolioAllocation.objects.filter(user=user).delete()
        
        # Calculate total value
        total_value = sum(account.balance for account in accounts)
        
        if total_value == 0:
            return Response({'message': 'No investments to calculate allocation'})
        
        # Group by type
        allocation_by_type = {}
        for account in accounts:
            account_type = account.type
            if account_type not in allocation_by_type:
                allocation_by_type[account_type] = Decimal('0')
            allocation_by_type[account_type] += account.balance
        
        # Create allocation records
        allocations = []
        for category, value in allocation_by_type.items():
            percentage = (value / total_value) * 100
            allocation = PortfolioAllocation.objects.create(
                user=user,
                category=category,
                percentage=percentage,
                value=value
            )
            allocations.append(allocation)
        
        serializer = PortfolioAllocationSerializer(allocations, many=True)
        return Response(serializer.data)


class InvestmentPerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing investment performance"""
    serializer_class = InvestmentPerformanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's investment performance"""
        return InvestmentPerformance.objects.filter(
            account__user=self.request.user
        ).select_related('account')
    
    @action(detail=False, methods=['post'])
    def generate_daily(self, request):
        """Generate daily performance records for all accounts"""
        user = request.user
        accounts = InvestmentAccount.objects.filter(user=user, is_active=True)
        
        today = timezone.now().date()
        created_records = []
        
        for account in accounts:
            # Check if record already exists for today
            existing = InvestmentPerformance.objects.filter(
                account=account, date=today
            ).first()
            
            if existing:
                continue
            
            # Calculate performance
            total_invested = Investment.objects.filter(
                account=account,
                transaction_type='BUY'
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
            
            total_value = account.balance
            profit_loss = total_value - total_invested
            profit_loss_percentage = (
                (profit_loss / total_invested * 100)
                if total_invested > 0 else Decimal('0')
            )
            
            # Create performance record
            performance = InvestmentPerformance.objects.create(
                account=account,
                date=today,
                total_value=total_value,
                total_invested=total_invested,
                profit_loss=profit_loss,
                profit_loss_percentage=profit_loss_percentage
            )
            created_records.append(performance)
        
        serializer = InvestmentPerformanceSerializer(created_records, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)