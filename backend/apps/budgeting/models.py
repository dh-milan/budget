import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class Budget(models.Model):
    """User budgets for spending categories"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='budgets'
    )
    category = models.CharField(max_length=100)
    limit_amount = models.DecimalField(max_digits=15, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    month_start = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'budgets'
        indexes = [
            models.Index(fields=['user', 'month_start']),
            models.Index(fields=['user', 'category', 'month_start'], name='unique_budget'),
        ]
        unique_together = ['user', 'category', 'month_start']
        ordering = ['-month_start', 'category']
    
    def __str__(self):
        return f"{self.user.email} - {self.category} - {self.month_start}"
    
    @property
    def remaining_amount(self):
        return self.limit_amount - self.spent_amount
    
    @property
    def percentage_used(self):
        if self.limit_amount > 0:
            return (self.spent_amount / self.limit_amount) * 100
        return 0


class SavingsGoal(models.Model):
    """User savings goals"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='savings_goals'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    target_amount = models.DecimalField(max_digits=15, decimal_places=2)
    current_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    target_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'savings_goals'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['user', 'target_date']),
        ]
        ordering = ['-target_date', 'name']
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"
    
    @property
    def progress_percentage(self):
        if self.target_amount > 0:
            return (self.current_amount / self.target_amount) * 100
        return 0
    
    @property
    def remaining_amount(self):
        return self.target_amount - self.current_amount


class Debt(models.Model):
    """User debts and liabilities"""
    DEBT_TYPES = [
        ('CREDIT_CARD', 'Credit Card'),
        ('LOAN', 'Loan'),
        ('MORTGAGE', 'Mortgage'),
        ('STUDENT_LOAN', 'Student Loan'),
        ('MEDICAL', 'Medical Debt'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='debts'
    )
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50, choices=DEBT_TYPES)
    total_balance = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Annual interest rate %")
    minimum_payment = models.DecimalField(max_digits=15, decimal_places=2)
    due_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'debts'
        indexes = [
            models.Index(fields=['user', 'type']),
            models.Index(fields=['user', 'is_active']),
        ]
        ordering = ['due_date', 'name']
    
    def __str__(self):
        return f"{self.user.email} - {self.name} ({self.type})"