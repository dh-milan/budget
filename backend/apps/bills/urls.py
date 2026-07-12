from django.urls import path
from .views import (
    BillListView,
    BillDetailView,
    BillPaymentListView,
    BillSummaryView,
    UpcomingBillsView,
    MarkBillPaidView,
)

urlpatterns = [
    # Bill endpoints
    path('bills/', BillListView.as_view(), name='bill-list'),
    path('bills/<uuid:bill_id>/', BillDetailView.as_view(), name='bill-detail'),
    path('bills/summary/', BillSummaryView.as_view(), name='bill-summary'),
    path('bills/upcoming/', UpcomingBillsView.as_view(), name='upcoming-bills'),
    path('bills/<uuid:bill_id>/mark-paid/', MarkBillPaidView.as_view(), name='mark-bill-paid'),
    
    # Bill payment endpoints
    path('bills/payments/', BillPaymentListView.as_view(), name='bill-payment-list'),
]