import json
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Account, Transaction, Category, Attachment
from .serializers import (
    AccountSerializer, AccountCreateSerializer,
    TransactionSerializer, TransactionCreateSerializer,
    CategorySerializer, CategoryCreateSerializer,
    AttachmentSerializer, BulkTransactionCreateSerializer,
    TransactionSummarySerializer, AccountBalanceSerializer
)
from apps.authentication.models import AuditLog


class AccountListView(APIView):
    """List and create accounts"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        accounts = Account.objects.filter(user=request.user, is_active=True)
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = AccountCreateSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.save(user=request.user)
            
            AuditLog.objects.create(
                user=request.user,
                action='ACCOUNT_CREATE',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={'account_id': str(account.id), 'name': account.name}
            )
            
            return Response(
                AccountSerializer(account).data, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class AccountDetailView(APIView):
    """Get, update, and delete accounts"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, account_id):
        try:
            account = Account.objects.get(id=account_id, user=request.user)
            serializer = AccountSerializer(account)
            return Response(serializer.data)
        except Account.DoesNotExist:
            return Response(
                {"error": "Account not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def patch(self, request, account_id):
        try:
            account = Account.objects.get(id=account_id, user=request.user)
            serializer = AccountSerializer(account, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                
                AuditLog.objects.create(
                    user=request.user,
                    action='ACCOUNT_UPDATE',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                    payload={'account_id': str(account.id)}
                )
                
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Account.DoesNotExist:
            return Response(
                {"error": "Account not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, account_id):
        try:
            account = Account.objects.get(id=account_id, user=request.user)
            account.is_active = False
            account.save()
            
            AuditLog.objects.create(
                user=request.user,
                action='ACCOUNT_DELETE',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={'account_id': str(account.id)}
            )
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Account.DoesNotExist:
            return Response(
                {"error": "Account not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class TransactionListView(APIView):
    """List and create transactions"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Filter parameters
        account_id = request.query_params.get('account_id')
        category = request.query_params.get('category')
        transaction_type = request.query_params.get('type')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        limit = int(request.query_params.get('limit', 100))
        offset = int(request.query_params.get('offset', 0))
        
        # Build query
        transactions = Transaction.objects.filter(
            account__user=request.user
        ).select_related('account')
        
        if account_id:
            transactions = transactions.filter(account_id=account_id)
        if category:
            transactions = transactions.filter(category=category)
        if transaction_type:
            transactions = transactions.filter(type=transaction_type)
        if start_date:
            transactions = transactions.filter(timestamp__gte=start_date)
        if end_date:
            transactions = transactions.filter(timestamp__lte=end_date)
        
        # Apply pagination
        total_count = transactions.count()
        transactions = transactions[offset:offset + limit]
        
        serializer = TransactionSerializer(transactions, many=True)
        
        return Response({
            'transactions': serializer.data,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        })
    
    def post(self, request):
        serializer = TransactionCreateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                # Get account with lock
                account = Account.objects.select_for_update().get(
                    id=serializer.validated_data['account'].id,
                    user=request.user
                )
                
                # Create transaction
                tx = serializer.save(account=account)
                
                # Update account balance
                if tx.type == 'EXPENSE':
                    account.balance -= tx.amount
                elif tx.type == 'INCOME':
                    account.balance += tx.amount
                account.save()
                
                AuditLog.objects.create(
                    user=request.user,
                    action='TRANSACTION_CREATE',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                    payload={
                        'transaction_id': str(tx.id),
                        'amount': str(tx.amount),
                        'type': tx.type
                    }
                )
            
            return Response(
                TransactionSerializer(tx).data, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class TransactionDetailView(APIView):
    """Get, update, and delete transactions"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, transaction_id):
        try:
            transaction = Transaction.objects.get(
                id=transaction_id, 
                account__user=request.user
            )
            serializer = TransactionSerializer(transaction)
            return Response(serializer.data)
        except Transaction.DoesNotExist:
            return Response(
                {"error": "Transaction not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def patch(self, request, transaction_id):
        try:
            tx = Transaction.objects.get(id=transaction_id, account__user=request.user)
            old_amount = tx.amount
            old_type = tx.type
            
            serializer = TransactionSerializer(tx, data=request.data, partial=True)
            if serializer.is_valid():
                with transaction.atomic():
                    # Reverse old transaction effect
                    account = Account.objects.select_for_update().get(id=tx.account_id)
                    if old_type == 'EXPENSE':
                        account.balance += old_amount
                    elif old_type == 'INCOME':
                        account.balance -= old_amount
                    
                    # Save updated transaction
                    updated_tx = serializer.save()
                    
                    # Apply new transaction effect
                    if updated_tx.type == 'EXPENSE':
                        account.balance -= updated_tx.amount
                    elif updated_tx.type == 'INCOME':
                        account.balance += updated_tx.amount
                    account.save()
                    
                    AuditLog.objects.create(
                        user=request.user,
                        action='TRANSACTION_UPDATE',
                        ip_address=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                        payload={'transaction_id': str(tx.id)}
                    )
                
                return Response(TransactionSerializer(updated_tx).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Transaction.DoesNotExist:
            return Response(
                {"error": "Transaction not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, transaction_id):
        try:
            tx = Transaction.objects.get(id=transaction_id, account__user=request.user)
            
            with transaction.atomic():
                # Reverse transaction effect on account
                account = Account.objects.select_for_update().get(id=tx.account_id)
                if tx.type == 'EXPENSE':
                    account.balance += tx.amount
                elif tx.type == 'INCOME':
                    account.balance -= tx.amount
                account.save()
                
                # Delete transaction
                tx.delete()
                
                AuditLog.objects.create(
                    user=request.user,
                    action='TRANSACTION_DELETE',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                    payload={'transaction_id': str(tx.id)}
                )
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Transaction.DoesNotExist:
            return Response(
                {"error": "Transaction not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class CategoryListView(APIView):
    """List and create categories"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        category_type = request.query_params.get('type')
        categories = Category.objects.filter(user=request.user, is_active=True)
        
        if category_type:
            categories = categories.filter(type=category_type)
        
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = CategoryCreateSerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save(user=request.user)
            
            AuditLog.objects.create(
                user=request.user,
                action='CATEGORY_CREATE',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={'category_id': str(category.id), 'name': category.name}
            )
            
            return Response(
                CategorySerializer(category).data, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class TransactionSummaryView(APIView):
    """Get transaction summary statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Date range parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        account_id = request.query_params.get('account_id')
        
        # Default to current month
        if not start_date or not end_date:
            today = timezone.now()
            start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        else:
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
        
        # Build query
        transactions = Transaction.objects.filter(
            account__user=request.user,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        if account_id:
            transactions = transactions.filter(account_id=account_id)
        
        # Calculate summary
        total_income = transactions.filter(type='INCOME').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        total_expenses = transactions.filter(type='EXPENSE').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Category breakdown
        category_breakdown = {}
        for tx in transactions.filter(type='EXPENSE'):
            category = tx.category
            if category not in category_breakdown:
                category_breakdown[category] = Decimal('0.00')
            category_breakdown[category] += tx.amount
        
        summary_data = {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_amount': total_income - total_expenses,
            'transaction_count': transactions.count(),
            'category_breakdown': category_breakdown,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }
        
        serializer = TransactionSummarySerializer(summary_data)
        return Response(serializer.data)


class BulkTransactionCreateView(APIView):
    """Create multiple transactions at once"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = BulkTransactionCreateSerializer(data=request.data)
        if serializer.is_valid():
            transactions_data = serializer.validated_data['transactions']
            created_transactions = []
            
            with transaction.atomic():
                for tx_data in transactions_data:
                    account = Account.objects.select_for_update().get(
                        id=tx_data['account'].id,
                        user=request.user
                    )
                    
                    tx = Transaction.objects.create(
                        account=account,
                        title=tx_data['title'],
                        amount=tx_data['amount'],
                        category=tx_data['category'],
                        type=tx_data['type'],
                        timestamp=tx_data['timestamp'],
                        note=tx_data.get('note', ''),
                        tags=tx_data.get('tags', ''),
                        is_recurring=tx_data.get('is_recurring', False)
                    )
                    
                    # Update account balance
                    if tx.type == 'EXPENSE':
                        account.balance -= tx.amount
                    elif tx.type == 'INCOME':
                        account.balance += tx.amount
                    account.save()
                    
                    created_transactions.append(tx)
            
            AuditLog.objects.create(
                user=request.user,
                action='BULK_TRANSACTION_CREATE',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={'count': len(created_transactions)}
            )
            
            response_serializer = TransactionSerializer(created_transactions, many=True)
            return Response(
                response_serializer.data, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class AttachmentUploadView(APIView):
    """Upload attachments for transactions"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, transaction_id):
        try:
            transaction = Transaction.objects.get(
                id=transaction_id, 
                account__user=request.user
            )
        except Transaction.DoesNotExist:
            return Response(
                {"error": "Transaction not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        file = request.FILES.get('file')
        if not file:
            return Response(
                {"error": "No file provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        attachment = Attachment.objects.create(
            transaction=transaction,
            file=file,
            file_type=file.content_type,
            file_size=file.size
        )
        
        AuditLog.objects.create(
            user=request.user,
            action='ATTACHMENT_UPLOAD',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
            payload={'transaction_id': str(transaction_id)}
        )
        
        serializer = AttachmentSerializer(attachment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')