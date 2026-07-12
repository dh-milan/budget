from rest_framework import serializers
from decimal import Decimal
from .models import Budget, SavingsGoal, Debt


class BudgetSerializer(serializers.ModelSerializer):
    """Serializer for Budget model"""
    remaining_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    percentage_used = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = Budget
        fields = [
            'id', 'category', 'limit_amount', 'spent_amount',
            'remaining_amount', 'percentage_used', 'month_start',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BudgetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating budgets"""
    class Meta:
        model = Budget
        fields = ['category', 'limit_amount', 'month_start']
    
    def validate_limit_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Budget limit must be greater than zero")
        return value


class SavingsGoalSerializer(serializers.ModelSerializer):
    """Serializer for SavingsGoal model"""
    progress_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = SavingsGoal
        fields = [
            'id', 'name', 'description', 'target_amount', 'current_amount',
            'remaining_amount', 'progress_percentage', 'target_date',
            'is_completed', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SavingsGoalCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating savings goals"""
    class Meta:
        model = SavingsGoal
        fields = ['name', 'description', 'target_amount', 'target_date']
    
    def validate_target_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Target amount must be greater than zero")
        return value


class DebtSerializer(serializers.ModelSerializer):
    """Serializer for Debt model"""
    class Meta:
        model = Debt
        fields = [
            'id', 'name', 'type', 'total_balance', 'interest_rate',
            'minimum_payment', 'due_date', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DebtCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating debts"""
    class Meta:
        model = Debt
        fields = ['name', 'type', 'total_balance', 'interest_rate', 'minimum_payment', 'due_date']
    
    def validate_total_balance(self, value):
        if value <= 0:
            raise serializers.ValidationError("Total balance must be greater than zero")
        return value
    
    def validate_interest_rate(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Interest rate must be between 0 and 100")
        return value


class BudgetSummarySerializer(serializers.Serializer):
    """Serializer for budget summary"""
    total_budget = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_spent = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_remaining = serializers.DecimalField(max_digits=15, decimal_places=2)
    budget_count = serializers.IntegerField()
    over_budget_count = serializers.IntegerField()
    category_breakdown = serializers.DictField()


class SavingsSummarySerializer(serializers.Serializer):
    """Serializer for savings summary"""
    total_goals = serializers.IntegerField()
    total_target = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_saved = serializers.DecimalField(max_digits=15, decimal_places=2)
    completed_goals = serializers.IntegerField()
    goals_progress = serializers.ListField()


class DebtSummarySerializer(serializers.Serializer):
    """Serializer for debt summary"""
    total_debt = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_minimum_payments = serializers.DecimalField(max_digits=15, decimal_places=2)
    debt_count = serializers.IntegerField()
    debt_breakdown = serializers.DictField()