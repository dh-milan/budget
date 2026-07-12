import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class Bill(models.Model):
    """User bills and recurring payments"""
    FREQUENCY_CHOICES = [
        ('WEEKLY', 'Weekly'),
        ('BIWEEKLY', 'Bi-weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('SEMI_ANNUALLY', 'Semi-annually'),
        ('ANNUALLY', 'Annually'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='bills'
    )
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    due_date = models.DateField()
    category = models.CharField(max_length=100)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='MONTHLY')
    is_paid = models.BooleanField(default=False)
    is_recurring = models.BooleanField(default=True)
    reminder_days = models.IntegerField(default=3, help_text="Days before due date to remind")
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bills'
        indexes = [
            models.Index(fields=['user', 'due_date']),
            models.Index(fields=['user', 'is_paid']),
            models.Index(fields=['user', 'is_active']),
        ]
        ordering = ['due_date', 'name']
    
    def __str__(self):
        return f"{self.user.email} - {self.name} - {self.due_date}"


class BillPayment(models.Model):
    """Track bill payments"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bill = models.ForeignKey(
        Bill, 
        on_delete=models.CASCADE, 
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=50, help_text="e.g., 'Credit Card', 'Bank Transfer'")
    transaction = models.ForeignKey(
        'ledger.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bill_payments'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'bill_payments'
        indexes = [
            models.Index(fields=['bill', 'payment_date']),
        ]
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.bill.name} - {self.payment_date} - {self.amount}"