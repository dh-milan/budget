from django.utils import timezone
from rest_framework import serializers

from .models import FinancialCalendarEvent


class FinancialCalendarEventSerializer(serializers.ModelSerializer):
    """Serializer for financial calendar events."""

    days_until = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    linked_bill_name = serializers.CharField(source='linked_bill.name', read_only=True)

    class Meta:
        model = FinancialCalendarEvent
        fields = [
            'id', 'title', 'event_type', 'event_date', 'amount', 'description',
            'is_reminder_enabled', 'reminder_days', 'is_recurring', 'metadata',
            'linked_bill', 'linked_bill_name', 'days_until', 'is_overdue',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'days_until', 'is_overdue', 'created_at', 'updated_at']

    def get_days_until(self, obj):
        return (obj.event_date - timezone.now().date()).days

    def get_is_overdue(self, obj):
        return obj.event_date < timezone.now().date()