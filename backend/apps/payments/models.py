import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class SubscriptionPlan(models.Model):
    """Subscription plans for the application"""
    PLAN_TYPES = [
        ('FREE', 'Free'),
        ('PRO', 'Pro'),
        ('ENTERPRISE', 'Enterprise'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True, choices=PLAN_TYPES)
    price_cents = models.IntegerField(help_text="Price in cents (e.g., 999 = $9.99)")
    interval_months = models.IntegerField(default=1, help_text="Billing interval in months")
    features = models.JSONField(default=dict, help_text="Plan features as JSON")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscription_plans'
        ordering = ['price_cents']
    
    def __str__(self):
        return f"{self.get_name_display()} - ${self.price_cents / 100:.2f}/{self.interval_months}mo"
    
    @property
    def price_dollars(self):
        return self.price_cents / 100


class UserSubscription(models.Model):
    """User subscription records"""
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('CANCELED', 'Canceled'),
        ('PAST_DUE', 'Past Due'),
        ('INCOMPLETE', 'Incomplete'),
        ('INCOMPLETE_EXPIRED', 'Incomplete Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='subscriptions'
    )
    plan = models.ForeignKey(
        SubscriptionPlan, 
        on_delete=models.PROTECT,
        related_name='user_subscriptions'
    )
    stripe_customer_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='ACTIVE')
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancel_at_period_end = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_subscriptions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['stripe_customer_id']),
            models.Index(fields=['stripe_subscription_id']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} - {self.status}"


class Payment(models.Model):
    """Payment history"""
    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('SUCCEEDED', 'Succeeded'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='payments'
    )
    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    amount_cents = models.IntegerField(help_text="Amount in cents")
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=50, choices=PAYMENT_STATUS)
    payment_method = models.CharField(max_length=50, help_text="e.g., 'card', 'paypal'")
    description = models.TextField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'payments'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['stripe_payment_intent_id']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.amount_cents / 100:.2f} {self.currency} - {self.status}"
    
    @property
    def amount_dollars(self):
        return self.amount_cents / 100


class Invoice(models.Model):
    """Invoice records"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='invoices'
    )
    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    stripe_invoice_id = models.CharField(max_length=255, unique=True)
    invoice_number = models.CharField(max_length=100)
    amount_cents = models.IntegerField()
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=50)
    invoice_pdf_url = models.URLField(null=True, blank=True)
    due_date = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'invoices'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['stripe_invoice_id']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - Invoice #{self.invoice_number}"