from django.contrib import admin

from .models import FinancialCalendarEvent


@admin.register(FinancialCalendarEvent)
class FinancialCalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'event_date', 'user', 'is_reminder_enabled')
    list_filter = ('event_type', 'is_reminder_enabled', 'is_recurring')
    search_fields = ('title', 'description')