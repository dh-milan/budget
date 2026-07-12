from django.contrib import admin

from .models import ReceiptScan


@admin.register(ReceiptScan)
class ReceiptScanAdmin(admin.ModelAdmin):
    list_display = ('merchant', 'status', 'total_amount', 'receipt_date', 'uploaded_at')
    list_filter = ('status', 'file_type', 'uploaded_at')
    search_fields = ('merchant', 'raw_text')