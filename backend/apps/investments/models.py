import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class InvestmentAccount(models.Model):
    """Investment accounts (stocks, ETFs, crypto, etc.)"""
    ACCOUNT_TYPES = [
        ('STOCKS', 'Stocks'),
        ('ETFS', 'ETFs'),
        ('MUTUAL_FUNDS', 'Mutual Funds'),
        ('CRYPTO', 'Cryptocurrency'),
        ('GOLD', 'Gold'),
        ('BONDS', 'Bonds'),
        ('REAL_ESTATE', 'Real Estate'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='investment_accounts'
    )
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='USD')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'investment_accounts'
        indexes = [
            models.Index(fields=['user', 'type']),
            models.Index(fields=['user', 'is_active']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.name} ({self.type})"


class Investment(models.Model):
    """Individual investment holdings"""
    TRANSACTION_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
        ('DIVIDEND', 'Dividend'),
        ('INTEREST', 'Interest'),
        ('FEE', 'Fee'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        InvestmentAccount, 
        on_delete=models.CASCADE, 
        related_name='investments'
    )
    symbol = models.CharField(max_length=20, help_text="Stock ticker or crypto symbol")
    name = models.CharField(max_length=100)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=15, decimal_places=6, help_text="Number of shares/units")
    price_per_unit = models.DecimalField(max_digits=15, decimal_places=2, help_text="Price per unit at transaction")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_date = models.DateTimeField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'investments'
        indexes = [
            models.Index(fields=['account', 'transaction_date']),
            models.Index(fields=['account', 'symbol']),
            models.Index(fields=['symbol']),
        ]
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.account.name} - {self.symbol} - {self.transaction_type}"


class PortfolioAllocation(models.Model):
    """Portfolio allocation by category"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='portfolio_allocations'
    )
    category = models.CharField(max_length=50, help_text="e.g., Stocks, Bonds, Crypto")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Allocation percentage")
    value = models.DecimalField(max_digits=15, decimal_places=2, help_text="Current value")
    target_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    calculated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'portfolio_allocations'
        indexes = [
            models.Index(fields=['user', 'calculated_at']),
        ]
        ordering = ['-percentage']
    
    def __str__(self):
        return f"{self.user.email} - {self.category} - {self.percentage}%"


class InvestmentPerformance(models.Model):
    """Track investment performance over time"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        InvestmentAccount, 
        on_delete=models.CASCADE, 
        related_name='performance_records'
    )
    date = models.DateField()
    total_value = models.DecimalField(max_digits=15, decimal_places=2)
    total_invested = models.DecimalField(max_digits=15, decimal_places=2)
    profit_loss = models.DecimalField(max_digits=15, decimal_places=2)
    profit_loss_percentage = models.DecimalField(max_digits=7, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'investment_performance'
        indexes = [
            models.Index(fields=['account', 'date']),
        ]
        unique_together = ['account', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.account.name} - {self.date} - {self.profit_loss_percentage}%"