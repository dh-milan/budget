import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class FinancialCalendarEvent(models.Model):
    """Financial calendar event such as bills, salary, goals, or subscriptions."""

    EVENT_TYPES = [
        ('BILL', 'Bill'),
        ('SALARY', 'Salary'),
        ('GOAL', 'Goal'),
        ('SUBSCRIPTION', 'Subscription'),
        ('OTHER', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='financial_calendar_events',
    )
    title = models.CharField(max_length=150)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    event_date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    description = models.TextField(blank=True)
    is_reminder_enabled = models.BooleanField(default=True)
    reminder_days = models.IntegerField(default=3)
    is_recurring = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    linked_bill = models.ForeignKey(
        'bills.Bill',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calendar_events',
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financial_calendar_events'
        indexes = [
            models.Index(fields=['user', 'event_date']),
            models.Index(fields=['user', 'event_type']),
            models.Index(fields=['user', 'is_reminder_enabled']),
        ]
        ordering = ['event_date', 'title']

    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.event_date})"