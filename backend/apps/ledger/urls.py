from django.urls import path
from .views import (
    AccountListView,
    AccountDetailView,
    TransactionListView,
    TransactionDetailView,
    CategoryListView,
    TransactionSummaryView,
    BulkTransactionCreateView,
    AttachmentUploadView,
    NetWorthView,
    CashFlowReportView,
    TransactionSearchView,
)

urlpatterns = [
    # Account endpoints
    path('accounts/', AccountListView.as_view(), name='account-list'),
    path('accounts/<uuid:account_id>/', AccountDetailView.as_view(), name='account-detail'),
    
    # Transaction endpoints
    path('transactions/', TransactionListView.as_view(), name='transaction-list'),
    path('transactions/<uuid:transaction_id>/', TransactionDetailView.as_view(), name='transaction-detail'),
    path('transactions/bulk/', BulkTransactionCreateView.as_view(), name='transaction-bulk-create'),
    path('transactions/summary/', TransactionSummaryView.as_view(), name='transaction-summary'),
    path('transactions/search/', TransactionSearchView.as_view(), name='transaction-search'),
    
    # Category endpoints
    path('categories/', CategoryListView.as_view(), name='category-list'),
    
    # Attachment endpoints
    path('transactions/<uuid:transaction_id>/attachments/', AttachmentUploadView.as_view(), name='attachment-upload'),
    
    # Analytics endpoints
    path('net-worth/', NetWorthView.as_view(), name='net-worth'),
    path('cash-flow/', CashFlowReportView.as_view(), name='cash-flow'),
]
