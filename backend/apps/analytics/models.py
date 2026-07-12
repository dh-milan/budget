import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class SpendingHeatmap(models.Model):
    """Daily spending data for heatmap visualization"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='spending_heatmaps'
    )
    date = models.DateField()
    total_spent = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    transaction_count = models.IntegerField(default=0)
    category_breakdown = models.JSONField(default=dict, help_text="Spending by category")
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'spending_heatmaps'
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
        unique_together = ['user', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.email} - {self.date} - ${self.total_spent}"


class FinancialScore(models.Model):
    """User financial health score"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='financial_scores'
    )
    overall_score = models.IntegerField(help_text="Score out of 100")
    savings_score = models.IntegerField(help_text="Score out of 100")
    budgeting_score = models.IntegerField(help_text="Score out of 100")
    debt_score = models.IntegerField(help_text="Score out of 100")
    investment_score = models.IntegerField(help_text="Score out of 100")
    insights = models.JSONField(default=list, help_text="List of insights")
    calculated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'financial_scores'
        indexes = [
            models.Index(fields=['user', 'calculated_at']),
        ]
        ordering = ['-calculated_at']
    
    def __str__(self):
        return f"{self.user.email} - Score: {self.overall_score}"


class ExpenseForecast(models.Model):
    """AI-predicted expenses"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='expense_forecasts'
    )
    forecast_date = models.DateField()
    predicted_amount = models.DecimalField(max_digits=15, decimal_places=2)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Confidence %")
    category_breakdown = models.JSONField(default=dict, help_text="Predicted spending by category")
    model_version = models.CharField(max_length=50, help_text="ML model version used")
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'expense_forecasts'
        indexes = [
            models.Index(fields=['user', 'forecast_date']),
        ]
        unique_together = ['user', 'forecast_date']
        ordering = ['-forecast_date']
    
    def __str__(self):
        return f"{self.user.email} - {self.forecast_date} - ${self.predicted_amount}"


class MonthlyReport(models.Model):
    """Generated monthly reports"""
    REPORT_TYPES = [
        ('MONTHLY', 'Monthly Summary'),
        ('TAX', 'Tax Report'),
        ('INCOME', 'Income Statement'),
        ('EXPENSE', 'Expense Report'),
        ('INVESTMENT', 'Investment Report'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='reports'
    )
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    file = models.FileField(upload_to='reports/%Y/%m/%d/', blank=True, null=True)
    file_format = models.CharField(max_length=10, help_text="PDF, XLSX, CSV")
    data = models.JSONField(default=dict, help_text="Report data")
    is_generated = models.BooleanField(default=False)
    generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'monthly_reports'
        indexes = [
            models.Index(fields=['user', 'report_type']),
            models.Index(fields=['user', 'start_date', 'end_date']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title} - {self.start_date} to {self.end_date}"


class CategoryTrend(models.Model):
    """Category spending trends over time"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='category_trends'
    )
    category = models.CharField(max_length=100)
    period = models.CharField(max_length=20, help_text="e.g., '2024-01', '2024-Q1'")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_count = models.IntegerField(default=0)
    percentage_of_total = models.DecimalField(max_digits=5, decimal_places=2)
    change_from_previous = models.DecimalField(max_digits=5, decimal_places=2, help_text="% change")
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'category_trends'
        indexes = [
            models.Index(fields=['user', 'category', 'period']),
        ]
        unique_together = ['user', 'category', 'period']
        ordering = ['-period', '-amount']
    
    def __str__(self):
        return f"{self.user.email} - {self.category} - {self.period} - ${self.amount}"