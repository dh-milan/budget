from rest_framework import serializers
from decimal import Decimal
from .models import InvestmentAccount, Investment, PortfolioAllocation, InvestmentPerformance


class InvestmentAccountSerializer(serializers.ModelSerializer):
    """Serializer for investment accounts"""
    total_value = serializers.SerializerMethodField()
    total_invested = serializers.SerializerMethodField()
    profit_loss = serializers.SerializerMethodField()
    profit_loss_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = InvestmentAccount
        fields = [
            'id', 'name', 'type', 'balance', 'currency', 
            'total_value', 'total_invested', 'profit_loss', 
            'profit_loss_percentage', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_value(self, obj):
        """Get current total value of the account"""
        return obj.balance
    
    def get_total_invested(self, obj):
        """Calculate total amount invested"""
        investments = obj.investments.filter(transaction_type='BUY')
        total = sum(inv.total_amount for inv in investments)
        return total
    
    def get_profit_loss(self, obj):
        """Calculate profit/loss"""
        total_invested = self.get_total_invested(obj)
        return obj.balance - total_invested
    
    def get_profit_loss_percentage(self, obj):
        """Calculate profit/loss percentage"""
        total_invested = self.get_total_invested(obj)
        if total_invested > 0:
            return ((obj.balance - total_invested) / total_invested) * 100
        return Decimal('0.00')


class InvestmentSerializer(serializers.ModelSerializer):
    """Serializer for individual investments"""
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_type = serializers.CharField(source='account.type', read_only=True)
    
    class Meta:
        model = Investment
        fields = [
            'id', 'account', 'account_name', 'account_type', 'symbol', 'name',
            'transaction_type', 'quantity', 'price_per_unit', 'total_amount',
            'transaction_date', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate(self, data):
        """Validate investment data"""
        # Calculate total amount
        quantity = data.get('quantity', Decimal('0'))
        price_per_unit = data.get('price_per_unit', Decimal('0'))
        expected_total = quantity * price_per_unit
        
        if data.get('total_amount') != expected_total:
            data['total_amount'] = expected_total
        
        return data


class PortfolioAllocationSerializer(serializers.ModelSerializer):
    """Serializer for portfolio allocation"""
    class Meta:
        model = PortfolioAllocation
        fields = [
            'id', 'category', 'percentage', 'value', 
            'target_percentage', 'calculated_at'
        ]
        read_only_fields = ['id', 'calculated_at']


class InvestmentPerformanceSerializer(serializers.ModelSerializer):
    """Serializer for investment performance"""
    account_name = serializers.CharField(source='account.name', read_only=True)
    
    class Meta:
        model = InvestmentPerformance
        fields = [
            'id', 'account', 'account_name', 'date', 'total_value',
            'total_invested', 'profit_loss', 'profit_loss_percentage', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PortfolioSummarySerializer(serializers.Serializer):
    """Serializer for portfolio summary"""
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_invested = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_profit_loss = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_profit_loss_percentage = serializers.DecimalField(max_digits=7, decimal_places=2)
    accounts = InvestmentAccountSerializer(many=True)
    allocation = PortfolioAllocationSerializer(many=True)
    recent_performance = InvestmentPerformanceSerializer(many=True)


class InvestmentInsightSerializer(serializers.Serializer):
    """Serializer for AI-generated investment insights"""
    insight_type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    priority = serializers.IntegerField()
    action_url = serializers.URLField(required=False)
    metadata = serializers.DictField(required=False)