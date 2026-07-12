import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Document(models.Model):
    """User documents (receipts, bills, warranties, tax docs)"""
    DOCUMENT_TYPES = [
        ('RECEIPT', 'Receipt'),
        ('BILL', 'Bill'),
        ('WARRANTY', 'Warranty'),
        ('TAX_DOCUMENT', 'Tax Document'),
        ('INVOICE', 'Invoice'),
        ('CONTRACT', 'Contract'),
        ('INSURANCE', 'Insurance'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    file_type = models.CharField(max_length=50, help_text="MIME type or file extension")
    file_size = models.IntegerField(help_text="File size in bytes")
    description = models.TextField(blank=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    transaction = models.ForeignKey(
        'ledger.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )
    is_cloud_synced = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents'
        indexes = [
            models.Index(fields=['user', 'document_type']),
            models.Index(fields=['user', 'uploaded_at']),
            models.Index(fields=['transaction']),
        ]
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.document_type})"


class DocumentTag(models.Model):
    """Custom tags for documents"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='document_tags'
    )
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#000000', help_text="Hex color code")
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'document_tags'
        indexes = [
            models.Index(fields=['user', 'name']),
        ]
        unique_together = ['user', 'name']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"