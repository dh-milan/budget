from django.urls import path
from .views import (
    SubscriptionPlanListView,
    SubscriptionStatusView,
    CreateCheckoutSessionView,
    StripeWebhookView,
    PaymentHistoryView,
    InvoiceListView,
)

urlpatterns = [
    # Subscription plans
    path('plans/', SubscriptionPlanListView.as_view(), name='subscription-plans'),
    
    # User subscription
    path('subscription/status/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path('subscription/create-checkout/', CreateCheckoutSessionView.as_view(), name='create-checkout'),
    
    # Webhooks
    path('webhooks/stripe/', StripeWebhookView.as_view(), name='stripe-webhook'),
    
    # Payment history
    path('payments/', PaymentHistoryView.as_view(), name='payment-history'),
    path('invoices/', InvoiceListView.as_view(), name='invoice-list'),
]