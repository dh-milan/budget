import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class ReceiptScan(models.Model):
    """Uploaded receipt that can be OCR processed and linked to a transaction."""

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSED', 'Processed'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='receipt_scans',
    )
    file = models.FileField(upload_to='receipts/%Y/%m/%d/')
    file_type = models.CharField(max_length=50)
    file_size = models.IntegerField()
    merchant = models.CharField(max_length=150, blank=True)
    receipt_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    items = models.JSONField(default=list, blank=True)
    category = models.CharField(max_length=100, blank=True)
    raw_text = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction = models.ForeignKey(
        'ledger.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receipt_scans',
    )
    error_message = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'receipt_scans'
        indexes = [
            models.Index(fields=['user', 'uploaded_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['transaction']),
        ]
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user.email} - {self.merchant or 'Receipt'}"