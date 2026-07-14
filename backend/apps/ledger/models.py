import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from django.core.validators import MinValueValidator


class Account(models.Model):
    """Financial accounts (checking, savings, credit cards, investments)"""
    ACCOUNT_TYPES = [
        ('CHECKING', 'Checking Account'),
        ('SAVINGS', 'Savings Account'),
        ('CREDIT_CARD', 'Credit Card'),
        ('INVESTMENT', 'Investment Account'),
        ('CASH', 'Cash'),
        ('LOAN', 'Loan'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,  # Changed from CASCADE to PROTECT
        related_name='accounts'
    )
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]  # Prevent negative balance
    )
    currency = models.CharField(max_length=3, default='USD')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts'
        indexes = [
            models.Index(fields=['user', 'type']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['user', 'balance']),  # Added for balance queries
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.name} ({self.type})"


class Transaction(models.Model):
    """Financial transactions"""
    TRANSACTION_TYPES = [
        ('EXPENSE', 'Expense'),
        ('INCOME', 'Income'),
        ('TRANSFER', 'Transfer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        Account, 
        on_delete=models.PROTECT,  # Changed from CASCADE to PROTECT - preserve transaction history
        related_name='transactions'
    )
    title = models.CharField(max_length=150)
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]  # Amount must be positive
    )
    category = models.CharField(max_length=100, db_index=True)
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    note = models.TextField(blank=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    is_recurring = models.BooleanField(default=False)
    receipt = models.FileField(upload_to='receipts/%Y/%m/%d/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'transactions'
        indexes = [
            models.Index(fields=['account', 'timestamp']),
            models.Index(fields=['account', 'category']),
            models.Index(fields=['account', 'type']),  # Added composite index
            models.Index(fields=['timestamp']),
            models.Index(fields=['category']),
            models.Index(fields=['type']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.account.name} - {self.title} - {self.amount}"


class Category(models.Model):
    """Transaction categories"""
    CATEGORY_TYPES = [
        ('EXPENSE', 'Expense'),
        ('INCOME', 'Income'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='categories'
    )
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    color = models.CharField(max_length=7, default='#000000', help_text="Hex color code")
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name or emoji")
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subcategories'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'categories'
        indexes = [
            models.Index(fields=['user', 'type']),
            models.Index(fields=['user', 'is_active']),
        ]
        unique_together = ['user', 'name', 'type']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.user.email} - {self.name} ({self.type})"


class Attachment(models.Model):
    """Attachments for transactions (receipts, invoices, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(
        Transaction, 
        on_delete=models.CASCADE,  # Keep CASCADE - attachments should be deleted with transaction
        related_name='attachments'
    )
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    file_type = models.CharField(max_length=50, help_text="MIME type or file extension")
    file_size = models.IntegerField(
        help_text="File size in bytes",
        validators=[MinValueValidator(1)]  # File size must be positive
    )
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'attachments'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.transaction.title} - {self.file_type}"