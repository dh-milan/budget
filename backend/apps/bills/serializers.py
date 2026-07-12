from rest_framework import serializers
from decimal import Decimal
from .models import Bill, BillPayment


class BillSerializer(serializers.ModelSerializer):
    """Serializer for Bill model"""
    days_until_due = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Bill
        fields = [
            'id', 'name', 'amount', 'due_date', 'category', 'frequency',
            'is_paid', 'is_recurring', 'reminder_days', 'notes',
            'days_until_due', 'is_overdue', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_days_until_due(self, obj):
        from datetime import date
        if obj.due_date:
            delta = (obj.due_date - date.today()).days
            return delta
        return None
    
    def get_is_overdue(self, obj):
        from datetime import date
        if obj.due_date and not obj.is_paid:
            return obj.due_date < date.today()
        return False


class BillCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bills"""
    class Meta:
        model = Bill
        fields = [
            'name', 'amount', 'due_date', 'category', 'frequency',
            'is_recurring', 'reminder_days', 'notes'
        ]
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Bill amount must be greater than zero")
        return value
    
    def validate_due_date(self, value):
        from datetime import date
        if value < date.today():
            raise serializers.ValidationError("Due date cannot be in the past")
        return value


class BillPaymentSerializer(serializers.ModelSerializer):
    """Serializer for BillPayment model"""
    bill_name = serializers.CharField(source='bill.name', read_only=True)
    
    class Meta:
        model = BillPayment
        fields = [
            'id', 'bill', 'bill_name', 'amount', 'payment_date',
            'payment_method', 'transaction', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BillPaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bill payments"""
    class Meta:
        model = BillPayment
        fields = ['bill', 'amount', 'payment_method', 'transaction', 'notes']
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Payment amount must be greater than zero")
        return value


class BillSummarySerializer(serializers.Serializer):
    """Serializer for bill summary"""
    total_bills = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    paid_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    unpaid_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    overdue_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    upcoming_bills = serializers.ListField()
    overdue_bills = serializers.ListField()


class UpcomingBillSerializer(serializers.Serializer):
    """Serializer for upcoming bills"""
    id = serializers.UUIDField()
    name = serializers.CharField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    due_date = serializers.DateField()
    days_until_due = serializers.IntegerField()
    category = serializers.CharField()
    is_paid = serializers.BooleanField()