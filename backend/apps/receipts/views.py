import uuid
from datetime import datetime, time

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ledger.models import Account, Transaction
from apps.ledger.serializers import TransactionSerializer

from .models import ReceiptScan
from .serializers import ReceiptScanSerializer
from .services import ReceiptProcessingService


class ReceiptUploadView(APIView):
    """Upload a receipt, extract data, and optionally create a transaction."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if 'receipt' not in request.FILES:
            return Response({'error': 'Receipt file is required'}, status=status.HTTP_400_BAD_REQUEST)

        receipt_file = request.FILES['receipt']
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
        if receipt_file.content_type not in allowed_types:
            return Response(
                {'error': 'Invalid file type. Please upload JPEG, PNG, or PDF'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if receipt_file.size > 10 * 1024 * 1024:
            return Response(
                {'error': 'File size too large. Maximum size is 10MB'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        auto_create_transaction = str(request.data.get('auto_create_transaction', 'true')).lower() == 'true'
        account_id = request.data.get('account_id')

        ext = receipt_file.name.split('.')[-1]
        filename = f"receipts/{request.user.id}/{uuid.uuid4()}.{ext}"
        path = default_storage.save(filename, ContentFile(receipt_file.read()))

        try:
            extracted_data = ReceiptProcessingService.process(default_storage.path(path))
            receipt_scan = ReceiptScan.objects.create(
                user=request.user,
                file=path,
                file_type=receipt_file.content_type,
                file_size=receipt_file.size,
                merchant=extracted_data.get('merchant', ''),
                receipt_date=datetime.fromisoformat(extracted_data['date']).date(),
                total_amount=extracted_data.get('amount', 0),
                items=extracted_data.get('items', []),
                category=extracted_data.get('category', 'Other'),
                raw_text=extracted_data.get('raw_text', ''),
                status='PROCESSED',
                processed_at=timezone.now(),
            )

            transaction = None
            if auto_create_transaction and extracted_data.get('amount', 0) > 0:
                account = None
                if account_id:
                    account = Account.objects.filter(id=account_id, user=request.user, is_active=True).first()
                if account is None:
                    account = Account.objects.filter(user=request.user, is_active=True).first()

                if account:
                    timestamp = timezone.now()
                    try:
                        parsed_date = datetime.fromisoformat(extracted_data['date']).date()
                        timestamp = timezone.make_aware(datetime.combine(parsed_date, time.min))
                    except Exception:
                        pass

                    transaction = Transaction.objects.create(
                        account=account,
                        title=f"Receipt: {extracted_data.get('merchant', 'Unknown Merchant')}",
                        amount=extracted_data.get('amount', 0),
                        category=extracted_data.get('category', 'Other'),
                        type='EXPENSE',
                        timestamp=timestamp,
                        note=f"Auto-categorized from receipt. Items: {', '.join(extracted_data.get('items', [])[:3])}",
                        tags='Receipt, Auto-Categorized',
                    )
                    receipt_scan.transaction = transaction
                    receipt_scan.save(update_fields=['transaction'])

            serializer = ReceiptScanSerializer(receipt_scan, context={'request': request})
            return Response(
                {
                    'message': 'Receipt processed successfully',
                    'scan': serializer.data,
                    'extracted_data': extracted_data,
                    'transaction': TransactionSerializer(transaction).data if transaction else None,
                    'requires_confirmation': transaction is None,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            receipt_scan = ReceiptScan.objects.create(
                user=request.user,
                file=path,
                file_type=receipt_file.content_type,
                file_size=receipt_file.size,
                status='FAILED',
                error_message=str(exc),
            )
            serializer = ReceiptScanSerializer(receipt_scan, context={'request': request})
            return Response(
                {
                    'error': f'Failed to process receipt: {exc}',
                    'scan': serializer.data,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )