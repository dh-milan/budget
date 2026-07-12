from rest_framework import serializers
from decimal import Decimal
from .models import SubscriptionPlan, UserSubscription, Payment, Invoice


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for SubscriptionPlan model"""
    price_dollars = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'price_cents', 'price_dollars', 'interval_months',
            'features', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for UserSubscription model"""
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_price = serializers.DecimalField(source='plan.price_dollars', read_only=True, max_digits=10, decimal_places=2)
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'plan', 'plan_name', 'plan_price', 'status',
            'current_period_start', 'current_period_end', 'cancel_at_period_end',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    amount_dollars = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'stripe_payment_intent_id', 'amount_cents', 'amount_dollars',
            'currency', 'status', 'payment_method', 'description',
            'paid_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model"""
    class Meta:
        model = Invoice
        fields = [
            'id', 'stripe_invoice_id', 'invoice_number', 'amount_cents',
            'currency', 'status', 'invoice_pdf_url', 'due_date', 'paid_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CreateCheckoutSessionSerializer(serializers.Serializer):
    """Serializer for creating Stripe checkout session"""
    plan_id = serializers.UUIDField(required=True)
    success_url = serializers.URLField(required=True)
    cancel_url = serializers.URLField(required=True)


class SubscriptionStatusSerializer(serializers.Serializer):
    """Serializer for subscription status response"""
    has_subscription = serializers.BooleanField()
    plan_name = serializers.CharField(allow_null=True)
    status = serializers.CharField(allow_null=True)
    current_period_end = serializers.DateTimeField(allow_null=True)
    cancel_at_period_end = serializers.BooleanField()


class PaymentHistorySerializer(serializers.Serializer):
    """Serializer for payment history summary"""
    total_payments = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    successful_payments = serializers.IntegerField()
    failed_payments = serializers.IntegerField()
    recent_payments = PaymentSerializer(many=True)