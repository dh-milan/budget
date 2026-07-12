from django.urls import path
from .views import (
    BillListView,
    BillDetailView,
    BillPaymentListView,
    BillSummaryView,
    UpcomingBillsView,
    MarkBillPaidView,
    GenerateRecurringBillsView,
    BillCalendarView,
)

urlpatterns = [
    # Bill endpoints
    path('bills/', BillListView.as_view(), name='bill-list'),
    path('bills/<uuid:bill_id>/', BillDetailView.as_view(), name='bill-detail'),
    path('bills/summary/', BillSummaryView.as_view(), name='bill-summary'),
    path('bills/upcoming/', UpcomingBillsView.as_view(), name='upcoming-bills'),
    path('bills/<uuid:bill_id>/mark-paid/', MarkBillPaidView.as_view(), name='mark-bill-paid'),
    path('bills/generate-recurring/', GenerateRecurringBillsView.as_view(), name='generate-recurring-bills'),
    path('bills/calendar/', BillCalendarView.as_view(), name='bill-calendar'),
    
    # Payment endpoints
    path('payments/', BillPaymentListView.as_view(), name='payment-list'),
]
