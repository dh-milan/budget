import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class ExpenseGroup(models.Model):
    """Groups for splitting expenses"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_expense_groups'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'expense_groups'
        indexes = [
            models.Index(fields=['created_by']),
            models.Index(fields=['is_active']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.created_by.email}"


class GroupMember(models.Model):
    """Members of expense groups"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        ExpenseGroup, 
        on_delete=models.CASCADE, 
        related_name='members'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='expense_group_memberships'
    )
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'group_members'
        indexes = [
            models.Index(fields=['group', 'is_active']),
        ]
        unique_together = ['group', 'user']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.group.name} - {self.user.email}"


class SplitExpense(models.Model):
    """Expenses to be split among group members"""
    EXPENSE_TYPES = [
        ('EQUAL', 'Equal Split'),
        ('PERCENTAGE', 'By Percentage'),
        ('EXACT', 'Exact Amounts'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        ExpenseGroup, 
        on_delete=models.CASCADE, 
        related_name='expenses'
    )
    title = models.CharField(max_length=150)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPES, default='EQUAL')
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    expense_date = models.DateField()
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='paid_expenses'
    )
    receipt = models.FileField(upload_to='split_expenses/%Y/%m/%d/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'split_expenses'
        indexes = [
            models.Index(fields=['group', 'expense_date']),
            models.Index(fields=['group', 'paid_by']),
        ]
        ordering = ['-expense_date']
    
    def __str__(self):
        return f"{self.group.name} - {self.title} - {self.total_amount}"


class ExpenseSplit(models.Model):
    """Individual splits for an expense"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expense = models.ForeignKey(
        SplitExpense, 
        on_delete=models.CASCADE, 
        related_name='splits'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='expense_splits'
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'expense_splits'
        indexes = [
            models.Index(fields=['expense', 'user']),
            models.Index(fields=['user', 'is_paid']),
        ]
        unique_together = ['expense', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.expense.title} - {self.user.email} - {self.amount}"


class Settlement(models.Model):
    """Settlements between group members"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        ExpenseGroup, 
        on_delete=models.CASCADE, 
        related_name='settlements'
    )
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='settlements_sent'
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='settlements_received'
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'settlements'
        indexes = [
            models.Index(fields=['group', 'is_completed']),
            models.Index(fields=['from_user', 'to_user']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.from_user.email} -> {self.to_user.email} - {self.amount}"