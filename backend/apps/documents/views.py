from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Document, DocumentTag
from .serializers import (
    DocumentSerializer,
    DocumentTagSerializer,
    DocumentSearchSerializer,
    DocumentStatsSerializer
)


class DocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing documents"""
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's documents"""
        queryset = Document.objects.filter(user=self.request.user)
        
        # Filter by document type
        document_type = self.request.query_params.get('document_type')
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(uploaded_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(uploaded_at__lte=end_date)
        
        # Filter by transaction
        has_transaction = self.request.query_params.get('has_transaction')
        if has_transaction is not None:
            if has_transaction.lower() == 'true':
                queryset = queryset.filter(transaction__isnull=False)
            else:
                queryset = queryset.filter(transaction__isnull=True)
        
        # Filter by cloud sync status
        is_cloud_synced = self.request.query_params.get('is_cloud_synced')
        if is_cloud_synced is not None:
            queryset = queryset.filter(is_cloud_synced=is_cloud_synced.lower() == 'true')
        
        return queryset
    
    def perform_create(self, serializer):
        """Create document for current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def link_transaction(self, request, pk=None):
        """Link document to a transaction"""
        document = self.get_object()
        transaction_id = request.data.get('transaction_id')
        
        if not transaction_id:
            return Response(
                {'error': 'transaction_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get transaction
        from apps.ledger.models import Transaction
        transaction = get_object_or_404(Transaction, id=transaction_id)
        
        # Verify transaction belongs to user
        if transaction.account.user != request.user:
            return Response(
                {'error': 'Transaction does not belong to you'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Link document
        document.transaction = transaction
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def unlink_transaction(self, request, pk=None):
        """Unlink document from transaction"""
        document = self.get_object()
        document.transaction = None
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """Search documents"""
        serializer = DocumentSearchSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        queryset = Document.objects.filter(user=request.user)
        
        # Search in title and description
        query = data.get('query')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query)
            )
        
        # Filter by document type
        document_type = data.get('document_type')
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        
        # Filter by tags
        tags = data.get('tags', [])
        if tags:
            for tag_name in tags:
                queryset = queryset.filter(tags__name__iexact=tag_name)
        
        # Filter by date range
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date:
            queryset = queryset.filter(uploaded_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(uploaded_at__lte=end_date)
        
        # Filter by transaction
        has_transaction = data.get('has_transaction')
        if has_transaction is not None:
            if has_transaction:
                queryset = queryset.filter(transaction__isnull=False)
            else:
                queryset = queryset.filter(transaction__isnull=True)
        
        # Filter by cloud sync
        is_cloud_synced = data.get('is_cloud_synced')
        if is_cloud_synced is not None:
            queryset = queryset.filter(is_cloud_synced=is_cloud_synced)
        
        # Return results
        documents = queryset.distinct()[:100]  # Limit to 100 results
        document_serializer = DocumentSerializer(documents, many=True)
        
        return Response({
            'count': queryset.count(),
            'results': document_serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get document statistics"""
        user = request.user
        documents = Document.objects.filter(user=user)
        
        # Total documents and size
        total_documents = documents.count()
        total_size_bytes = sum(doc.file_size for doc in documents)
        total_size_mb = round(total_size_bytes / (1024 * 1024), 2)
        
        # By type
        by_type = {}
        for doc_type, doc_type_label in Document.DOCUMENT_TYPES:
            count = documents.filter(document_type=doc_type).count()
            if count > 0:
                by_type[doc_type_label] = count
        
        # By month (last 12 months)
        by_month = {}
        for i in range(12):
            month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
            month_key = month_start.strftime('%Y-%m')
            count = documents.filter(
                uploaded_at__year=month_start.year,
                uploaded_at__month=month_start.month
            ).count()
            if count > 0:
                by_month[month_key] = count
        
        # Cloud sync stats
        cloud_synced_count = documents.filter(is_cloud_synced=True).count()
        pending_sync_count = documents.filter(is_cloud_synced=False).count()
        
        data = {
            'total_documents': total_documents,
            'total_size_mb': total_size_mb,
            'by_type': by_type,
            'by_month': by_month,
            'cloud_synced_count': cloud_synced_count,
            'pending_sync_count': pending_sync_count
        }
        
        serializer = DocumentStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """Upload multiple documents"""
        files = request.FILES.getlist('files')
        document_type = request.data.get('document_type', 'OTHER')
        
        if not files:
            return Response(
                {'error': 'No files provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_documents = []
        
        for file in files:
            # Create document
            document = Document.objects.create(
                user=request.user,
                title=file.name,
                document_type=document_type,
                file=file,
                file_type=file.content_type,
                file_size=file.size
            )
            
            uploaded_documents.append(document)
        
        serializer = DocumentSerializer(uploaded_documents, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def mark_synced(self, request, pk=None):
        """Mark document as cloud synced"""
        document = self.get_object()
        document.is_cloud_synced = True
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)


class DocumentTagViewSet(viewsets.ModelViewSet):
    """ViewSet for managing document tags"""
    serializer_class = DocumentTagSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's document tags"""
        return DocumentTag.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create tag for current user"""
        serializer.save(user=self.request.user)