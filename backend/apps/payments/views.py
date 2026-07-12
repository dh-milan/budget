import stripe
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from decimal import Decimal

from .models import SubscriptionPlan, UserSubscription, Payment, Invoice
from .serializers import (
    SubscriptionPlanSerializer, UserSubscriptionSerializer,
    PaymentSerializer, InvoiceSerializer,
    CreateCheckoutSessionSerializer, SubscriptionStatusSerializer,
    PaymentHistorySerializer
)
from apps.authentication.models import AuditLog


class SubscriptionPlanListView(APIView):
    """List all available subscription plans"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True)
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)


class SubscriptionStatusView(APIView):
    """Get current user's subscription status"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            subscription = UserSubscription.objects.get(
                user=request.user, 
                is_active=True
            )
            serializer = SubscriptionStatusSerializer({
                'has_subscription': True,
                'plan_name': subscription.plan.name,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end,
                'cancel_at_period_end': subscription.cancel_at_period_end
            })
            return Response(serializer.data)
        except UserSubscription.DoesNotExist:
            return Response({
                'has_subscription': False,
                'plan_name': None,
                'status': None,
                'current_period_end': None,
                'cancel_at_period_end': False
            })


class CreateCheckoutSessionView(APIView):
    """Create Stripe checkout session for subscription"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CreateCheckoutSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        plan_id = serializer.validated_data['plan_id']
        success_url = serializer.validated_data['success_url']
        cancel_url = serializer.validated_data['cancel_url']
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {"error": "Invalid subscription plan"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Create or get Stripe customer
            user = request.user
            stripe_customer_id = None
            
            # Check if user already has a subscription
            existing_subscription = UserSubscription.objects.filter(
                user=user, 
                is_active=True
            ).first()
            
            if existing_subscription and existing_subscription.stripe_customer_id:
                stripe_customer_id = existing_subscription.stripe_customer_id
            else:
                # Create new Stripe customer
                customer = stripe.Customer.create(
                    email=user.email,
                    name=user.full_name,
                    metadata={'user_id': str(user.id)}
                )
                stripe_customer_id = customer.id
            
            # Create Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                customer=stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'WealthFlow {plan.get_name_display()} Plan',
                        },
                        'unit_amount': plan.price_cents,
                        'recurring': {
                            'interval': 'month' if plan.interval_months == 1 else 'year',
                        },
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user.id),
                    'plan_id': str(plan.id)
                }
            )
            
            AuditLog.objects.create(
                user=user,
                action='CHECKOUT_SESSION_CREATE',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={'plan_id': str(plan.id)}
            )
            
            return Response({
                'session_id': checkout_session.id,
                'url': checkout_session.url
            })
            
        except stripe.error.StripeError as e:
            return Response(
                {"error": f"Stripe error: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to create checkout session: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class StripeWebhookView(APIView):
    """Handle Stripe webhooks"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, 
                sig_header, 
                settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        # Handle the event
        event_type = event['type']
        event_data = event['data']['object']
        
        try:
            if event_type == 'checkout.session.completed':
                self.handle_checkout_completed(event_data)
            elif event_type == 'customer.subscription.updated':
                self.handle_subscription_updated(event_data)
            elif event_type == 'customer.subscription.deleted':
                self.handle_subscription_deleted(event_data)
            elif event_type == 'invoice.payment_succeeded':
                self.handle_payment_succeeded(event_data)
            elif event_type == 'invoice.payment_failed':
                self.handle_payment_failed(event_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(status=status.HTTP_200_OK)
    
    def handle_checkout_completed(self, session_data):
        """Handle successful checkout"""
        user_id = session_data['metadata']['user_id']
        plan_id = session_data['metadata']['plan_id']
        stripe_customer_id = session_data['customer']
        stripe_subscription_id = session_data['subscription']
        
        # Get user and plan
        User = settings.AUTH_USER_MODEL
        user = User.objects.get(id=user_id)
        plan = SubscriptionPlan.objects.get(id=plan_id)
        
        # Get subscription details from Stripe
        stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        
        # Create or update subscription
        subscription, created = UserSubscription.objects.update_or_create(
            stripe_subscription_id=stripe_subscription_id,
            defaults={
                'user': user,
                'plan': plan,
                'stripe_customer_id': stripe_customer_id,
                'status': stripe_subscription['status'].upper(),
                'current_period_start': timezone.datetime.fromtimestamp(
                    stripe_subscription['current_period_start'], 
                    tz=timezone.utc
                ),
                'current_period_end': timezone.datetime.fromtimestamp(
                    stripe_subscription['current_period_end'], 
                    tz=timezone.utc
                ),
                'is_active': True
            }
        )
    
    def handle_subscription_updated(self, subscription_data):
        """Handle subscription updates"""
        stripe_subscription_id = subscription_data['id']
        
        try:
            subscription = UserSubscription.objects.get(
                stripe_subscription_id=stripe_subscription_id
            )
            subscription.status = subscription_data['status'].upper()
            subscription.current_period_start = timezone.datetime.fromtimestamp(
                subscription_data['current_period_start'],
                tz=timezone.utc
            )
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                subscription_data['current_period_end'],
                tz=timezone.utc
            )
            subscription.cancel_at_period_end = subscription_data.get('cancel_at_period_end', False)
            subscription.save()
        except UserSubscription.DoesNotExist:
            pass
    
    def handle_subscription_deleted(self, subscription_data):
        """Handle subscription cancellation"""
        stripe_subscription_id = subscription_data['id']
        
        try:
            subscription = UserSubscription.objects.get(
                stripe_subscription_id=stripe_subscription_id
            )
            subscription.status = 'CANCELED'
            subscription.is_active = False
            subscription.save()
        except UserSubscription.DoesNotExist:
            pass
    
    def handle_payment_succeeded(self, invoice_data):
        """Handle successful payment"""
        stripe_invoice_id = invoice_data['id']
        
        # Check if invoice already exists
        if Invoice.objects.filter(stripe_invoice_id=stripe_invoice_id).exists():
            return
        
        # Get customer and subscription
        customer_id = invoice_data.get('customer')
        subscription_id = invoice_data.get('subscription')
        
        if not customer_id or not subscription_id:
            return
        
        try:
            user = settings.AUTH_USER_MODEL.objects.get(
                subscriptions__stripe_customer_id=customer_id
            )
            subscription = UserSubscription.objects.get(
                stripe_subscription_id=subscription_id
            )
            
            # Create invoice record
            Invoice.objects.create(
                user=user,
                subscription=subscription,
                stripe_invoice_id=stripe_invoice_id,
                invoice_number=invoice_data['number'],
                amount_cents=invoice_data['amount_paid'],
                currency=invoice_data['currency'].upper(),
                status=invoice_data['status'],
                invoice_pdf_url=invoice_data.get('invoice_pdf'),
                due_date=timezone.datetime.fromtimestamp(
                    invoice_data['due_date'],
                    tz=timezone.utc
                ),
                paid_at=timezone.datetime.fromtimestamp(
                    invoice_data['status_transitions']['paid_at'],
                    tz=timezone.utc
                ) if invoice_data.get('status_transitions', {}).get('paid_at') else None
            )
            
            # Create payment record
            Payment.objects.create(
                user=user,
                subscription=subscription,
                stripe_payment_intent_id=invoice_data.get('payment_intent', ''),
                amount_cents=invoice_data['amount_paid'],
                currency=invoice_data['currency'].upper(),
                status='SUCCEEDED',
                payment_method='card',
                description=f"Payment for {subscription.plan.name} plan",
                paid_at=timezone.now()
            )
            
        except (settings.AUTH_USER_MODEL.DoesNotExist, UserSubscription.DoesNotExist):
            pass
    
    def handle_payment_failed(self, invoice_data):
        """Handle failed payment"""
        stripe_invoice_id = invoice_data['id']
        customer_id = invoice_data.get('customer')
        
        if not customer_id:
            return
        
        try:
            user = settings.AUTH_USER_MODEL.objects.get(
                subscriptions__stripe_customer_id=customer_id
            )
            subscription = UserSubscription.objects.get(
                user=user,
                is_active=True
            )
            
            # Create payment record
            Payment.objects.create(
                user=user,
                subscription=subscription,
                stripe_payment_intent_id=invoice_data.get('payment_intent', ''),
                amount_cents=invoice_data['amount_due'],
                currency=invoice_data['currency'].upper(),
                status='FAILED',
                payment_method='card',
                description=f"Failed payment for {subscription.plan.name} plan"
            )
            
        except (settings.AUTH_USER_MODEL.DoesNotExist, UserSubscription.DoesNotExist):
            pass


class PaymentHistoryView(APIView):
    """Get user's payment history"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        payments = Payment.objects.filter(user=request.user)
        
        total_amount = payments.aggregate(
            total=Sum('amount_cents')
        )['total'] or 0
        
        successful_payments = payments.filter(status='SUCCEEDED').count()
        failed_payments = payments.filter(status='FAILED').count()
        
        recent_payments = payments[:20]
        
        summary_data = {
            'total_payments': payments.count(),
            'total_amount': total_amount / 100,  # Convert to dollars
            'successful_payments': successful_payments,
            'failed_payments': failed_payments,
            'recent_payments': recent_payments
        }
        
        serializer = PaymentHistorySerializer(summary_data)
        return Response(serializer.data)


class InvoiceListView(APIView):
    """List user's invoices"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        invoices = Invoice.objects.filter(user=request.user)
        serializer = InvoiceSerializer(invoices, many=True)
        return Response(serializer.data)