from rest_framework import serializers
from .models import FamilyGroup, FamilyMember, SharedBudget, SharedGoal


class FamilyMemberSerializer(serializers.ModelSerializer):
    """Serializer for family members"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = FamilyMember
        fields = [
            'id', 'family', 'user', 'user_email', 'user_name', 
            'role', 'is_active', 'joined_at'
        ]
        read_only_fields = ['id', 'joined_at']


class FamilyGroupSerializer(serializers.ModelSerializer):
    """Serializer for family groups"""
    member_count = serializers.SerializerMethodField()
    members = FamilyMemberSerializer(many=True, read_only=True)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    
    class Meta:
        model = FamilyGroup
        fields = [
            'id', 'name', 'created_by', 'created_by_email', 
            'member_count', 'members', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        """Get count of active members"""
        return obj.members.filter(is_active=True).count()


class SharedBudgetSerializer(serializers.ModelSerializer):
    """Serializer for shared budgets"""
    family_name = serializers.CharField(source='family.name', read_only=True)
    remaining_amount = serializers.SerializerMethodField()
    percentage_used = serializers.SerializerMethodField()
    
    class Meta:
        model = SharedBudget
        fields = [
            'id', 'family', 'family_name', 'category', 'limit_amount',
            'spent_amount', 'remaining_amount', 'percentage_used',
            'month_start', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_remaining_amount(self, obj):
        """Calculate remaining budget"""
        return obj.limit_amount - obj.spent_amount
    
    def get_percentage_used(self, obj):
        """Calculate percentage of budget used"""
        if obj.limit_amount > 0:
            return (obj.spent_amount / obj.limit_amount) * 100
        return 0


class SharedGoalSerializer(serializers.ModelSerializer):
    """Serializer for shared goals"""
    family_name = serializers.CharField(source='family.name', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = SharedGoal
        fields = [
            'id', 'family', 'family_name', 'name', 'description',
            'target_amount', 'current_amount', 'progress_percentage',
            'remaining_amount', 'target_date', 'is_completed', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_progress_percentage(self, obj):
        """Calculate progress percentage"""
        if obj.target_amount > 0:
            return (obj.current_amount / obj.target_amount) * 100
        return 0
    
    def get_remaining_amount(self, obj):
        """Calculate remaining amount"""
        return obj.target_amount - obj.current_amount


class FamilyDashboardSerializer(serializers.Serializer):
    """Serializer for family dashboard"""
    family = FamilyGroupSerializer()
    total_members = serializers.IntegerField()
    active_budgets = SharedBudgetSerializer(many=True)
    active_goals = SharedGoalSerializer(many=True)
    total_budget_spent = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_goal_progress = serializers.DecimalField(max_digits=15, decimal_places=2)