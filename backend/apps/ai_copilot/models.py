import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class AIConversation(models.Model):
    """AI chat conversations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='ai_conversations'
    )
    title = models.CharField(max_length=255, default='New Discussion')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_conversations'
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"


class AIMessage(models.Model):
    """AI chat messages"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('model', 'AI Model'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        AIConversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'ai_messages'
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.conversation.title} - {self.role} - {self.created_at}"


class AIInsight(models.Model):
    """AI-generated insights for users"""
    INSIGHT_TYPES = [
        ('SPENDING_PATTERN', 'Spending Pattern'),
        ('BUDGET_ALERT', 'Budget Alert'),
        ('SAVINGS_OPPORTUNITY', 'Savings Opportunity'),
        ('SUBSCRIPTION_DETECTED', 'Subscription Detected'),
        ('DUPLICATE_CHARGE', 'Duplicate Charge'),
        ('BILL_REMINDER', 'Bill Reminder'),
        ('FINANCIAL_HEALTH', 'Financial Health'),
        ('GOAL_PROGRESS', 'Goal Progress'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='ai_insights'
    )
    insight_type = models.CharField(max_length=50, choices=INSIGHT_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.IntegerField(default=0, help_text="Higher number = higher priority")
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    action_url = models.URLField(blank=True, null=True, help_text="URL to navigate when clicked")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'ai_insights'
        indexes = [
            models.Index(fields=['user', 'is_read', 'is_dismissed']),
            models.Index(fields=['user', 'insight_type']),
            models.Index(fields=['user', 'priority']),
        ]
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"


class AIUsageLog(models.Model):
    """Track AI API usage for monitoring and billing"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='ai_usage_logs'
    )
    endpoint = models.CharField(max_length=100, help_text="API endpoint called")
    tokens_used = models.IntegerField(default=0, help_text="Number of tokens consumed")
    response_time_ms = models.IntegerField(help_text="Response time in milliseconds")
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'ai_usage_logs'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['endpoint', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.endpoint} - {self.created_at}"