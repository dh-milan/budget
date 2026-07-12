from rest_framework import serializers
from decimal import Decimal
from .models import ExpenseGroup, GroupMember, SplitExpense, ExpenseSplit, Settlement


class GroupMemberSerializer(serializers.ModelSerializer):
    """Serializer for group members"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = GroupMember
        fields = [
            'id', 'group', 'user', 'user_email', 'user_name', 
            'is_active', 'joined_at'
        ]
        read_only_fields = ['id', 'joined_at']


class ExpenseSplitSerializer(serializers.ModelSerializer):
    """Serializer for expense splits"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = ExpenseSplit
        fields = [
            'id', 'expense', 'user', 'user_email', 'user_name',
            'amount', 'is_paid', 'paid_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SplitExpenseSerializer(serializers.ModelSerializer):
    """Serializer for split expenses"""
    splits = ExpenseSplitSerializer(many=True, read_only=True)
    paid_by_email = serializers.CharField(source='paid_by.email', read_only=True)
    paid_by_name = serializers.CharField(source='paid_by.get_full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    split_details = serializers.SerializerMethodField()
    
    class Meta:
        model = SplitExpense
        fields = [
            'id', 'group', 'group_name', 'title', 'total_amount', 'expense_type',
            'category', 'description', 'expense_date', 'paid_by', 'paid_by_email',
            'paid_by_name', 'receipt', 'splits', 'split_details', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_split_details(self, obj):
        """Get split calculation details"""
        splits = obj.splits.all()
        total_split = sum(split.amount for split in splits)
        unpaid_count = splits.filter(is_paid=False).count()
        
        return {
            'total_split': total_split,
            'unpaid_count': unpaid_count,
            'paid_count': splits.filter(is_paid=True).count(),
            'is_balanced': abs(total_split - obj.total_amount) < Decimal('0.01')
        }


class SettlementSerializer(serializers.ModelSerializer):
    """Serializer for settlements"""
    from_user_email = serializers.CharField(source='from_user.email', read_only=True)
    from_user_name = serializers.CharField(source='from_user.get_full_name', read_only=True)
    to_user_email = serializers.CharField(source='to_user.email', read_only=True)
    to_user_name = serializers.CharField(source='to_user.get_full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    
    class Meta:
        model = Settlement
        fields = [
            'id', 'group', 'group_name', 'from_user', 'from_user_email',
            'from_user_name', 'to_user', 'to_user_email', 'to_user_name',
            'amount', 'is_completed', 'completed_at', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ExpenseGroupSerializer(serializers.ModelSerializer):
    """Serializer for expense groups"""
    member_count = serializers.SerializerMethodField()
    members = GroupMemberSerializer(many=True, read_only=True)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    total_expenses = serializers.SerializerMethodField()
    pending_settlements = serializers.SerializerMethodField()
    
    class Meta:
        model = ExpenseGroup
        fields = [
            'id', 'name', 'description', 'created_by', 'created_by_email',
            'member_count', 'members', 'total_expenses', 'pending_settlements',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        """Get count of active members"""
        return obj.members.filter(is_active=True).count()
    
    def get_total_expenses(self, obj):
        """Get total expenses in this group"""
        return obj.expenses.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')
    
    def get_pending_settlements(self, obj):
        """Get pending settlements amount"""
        return obj.settlements.filter(
            is_completed=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')


class CreateSplitExpenseSerializer(serializers.Serializer):
    """Serializer for creating split expenses with automatic split calculation"""
    group_id = serializers.UUIDField()
    title = serializers.CharField(max_length=150)
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    expense_type = serializers.ChoiceField(choices=SplitExpense.EXPENSE_TYPES, default='EQUAL')
    category = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False)
    expense_date = serializers.DateField()
    paid_by_id = serializers.UUIDField()
    splits = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="List of {user_id, amount} for EXACT type"
    )
    receipt = serializers.FileField(required=False)


class SettlementBalanceSerializer(serializers.Serializer):
    """Serializer for settlement balances"""
    user_id = serializers.UUIDField()
    user_email = serializers.CharField()
    user_name = serializers.CharField()
    total_paid = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_share = serializers.DecimalField(max_digits=15, decimal_places=2)
    balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    # Positive balance = user should receive money
    # Negative balance = user should pay money


class GroupDashboardSerializer(serializers.Serializer):
    """Serializer for group dashboard"""
    group = ExpenseGroupSerializer()
    total_expenses = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_settlements = serializers.DecimalField(max_digits=15, decimal_places=2)
    recent_expenses = SplitExpenseSerializer(many=True)
    pending_settlements = SettlementSerializer(many=True)
    member_balances = SettlementBalanceSerializer(many=True)