from rest_framework import serializers

from .models import ReceiptScan


class ReceiptScanSerializer(serializers.ModelSerializer):
    """Serializer for receipt scans and extracted receipt data."""

    file_url = serializers.SerializerMethodField()
    transaction_title = serializers.CharField(source='transaction.title', read_only=True)

    class Meta:
        model = ReceiptScan
        fields = [
            'id', 'file', 'file_url', 'file_type', 'file_size', 'merchant',
            'receipt_date', 'total_amount', 'items', 'category', 'raw_text',
            'status', 'transaction', 'transaction_title', 'error_message',
            'uploaded_at', 'processed_at',
        ]
        read_only_fields = [
            'id', 'file_url', 'merchant', 'receipt_date', 'total_amount',
            'items', 'category', 'raw_text', 'status', 'transaction',
            'error_message', 'uploaded_at', 'processed_at',
        ]

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None