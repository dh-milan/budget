from datetime import date, timedelta
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from decimal import Decimal

from .models import Bill, BillPayment
from .serializers import (
    BillSerializer, BillCreateSerializer,
    BillPaymentSerializer, BillPaymentCreateSerializer,
    BillSummarySerializer, UpcomingBillSerializer
)
from apps.authentication.models import AuditLog


class BillListView(APIView):
    """List and create bills"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        is_paid = request.query_params.get('is_paid')
        is_active = request.query_params.get('is_active', 'true')
        
        bills = Bill.objects.filter(user=request.user)
        
        if is_paid is not None:
            bills = bills.filter(is_paid=is_paid.lower() == 'true')
        
        if is_active.lower() == 'true':
            bills = bills.filter(is_active=True)
        
        serializer = BillSerializer(bills, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = BillCreateSerializer(data=request.data)
        if serializer.is_valid():
            bill = serializer.save(user=request.user)
            
            AuditLog.objects.create(
                user=request.user,
                action='BILL_CREATE',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={'bill_id': str(bill.id), 'name': bill.name}
            )
            
            return Response(
                BillSerializer(bill).data, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class BillDetailView(APIView):
    """Get, update, and delete bills"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, bill_id):
        try:
            bill = Bill.objects.get(id=bill_id, user=request.user)
            serializer = BillSerializer(bill)
            return Response(serializer.data)
        except Bill.DoesNotExist:
            return Response(
                {"error": "Bill not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def patch(self, request, bill_id):
        try:
            bill = Bill.objects.get(id=bill_id, user=request.user)
            serializer = BillCreateSerializer(bill, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                
                AuditLog.objects.create(
                    user=request.user,
                    action='BILL_UPDATE',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                    payload={'bill_id': str(bill.id)}
                )
                
                return Response(BillSerializer(bill).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Bill.DoesNotExist:
            return Response(
                {"error": "Bill not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, bill_id):
        try:
            bill = Bill.objects.get(id=bill_id, user=request.user)
            bill.is_active = False
            bill.save()
            
            AuditLog.objects.create(
                user=request.user,
                action='BILL_DELETE',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={'bill_id': str(bill.id)}
            )
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Bill.DoesNotExist:
            return Response(
                {"error": "Bill not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class BillPaymentListView(APIView):
    """List and create bill payments"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        bill_id = request.query_params.get('bill_id')
        payments = BillPayment.objects.filter(bill__user=request.user)
        
        if bill_id:
            payments = payments.filter(bill_id=bill_id)
        
        payments = payments.order_by('-payment_date')
        serializer = BillPaymentSerializer(payments, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = BillPaymentCreateSerializer(data=request.data)
        if serializer.is_valid():
            bill = serializer.validated_data['bill']
            
            # Verify bill belongs to user
            if bill.user != request.user:
                return Response(
                    {"error": "Bill not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            payment = serializer.save()
            
            # Mark bill as paid
            bill.is_paid = True
            bill.save()
            
            AuditLog.objects.create(
                user=request.user,
                action='BILL_PAYMENT_CREATE',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={
                    'bill_id': str(bill.id),
                    'payment_id': str(payment.id),
                    'amount': str(payment.amount)
                }
            )
            
            return Response(
                BillPaymentSerializer(payment).data, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class BillSummaryView(APIView):
    """Get bill summary statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        today = date.today()
        
        # Get all active bills
        bills = Bill.objects.filter(user=request.user, is_active=True)
        
        # Calculate totals
        total_amount = sum(b.amount for b in bills)
        paid_amount = sum(b.amount for b in bills if b.is_paid)
        unpaid_amount = total_amount - paid_amount
        
        # Overdue bills
        overdue_bills = bills.filter(due_date__lt=today, is_paid=False)
        overdue_amount = sum(b.amount for b in overdue_bills)
        
        # Upcoming bills (next 30 days)
        upcoming_date = today + timedelta(days=30)
        upcoming_bills = bills.filter(
            due_date__gte=today,
            due_date__lte=upcoming_date,
            is_paid=False
        ).order_by('due_date')[:10]
        
        upcoming_list = []
        for bill in upcoming_bills:
            upcoming_list.append({
                'id': str(bill.id),
                'name': bill.name,
                'amount': str(bill.amount),
                'due_date': bill.due_date.isoformat(),
                'days_until_due': (bill.due_date - today).days,
                'category': bill.category,
                'is_paid': bill.is_paid
            })
        
        overdue_list = []
        for bill in overdue_bills:
            overdue_list.append({
                'id': str(bill.id),
                'name': bill.name,
                'amount': str(bill.amount),
                'due_date': bill.due_date.isoformat(),
                'days_overdue': (today - bill.due_date).days,
                'category': bill.category
            })
        
        summary_data = {
            'total_bills': bills.count(),
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'unpaid_amount': unpaid_amount,
            'overdue_amount': overdue_amount,
            'upcoming_bills': upcoming_list,
            'overdue_bills': overdue_list
        }
        
        serializer = BillSummarySerializer(summary_data)
        return Response(serializer.data)


class UpcomingBillsView(APIView):
    """Get upcoming bills for the next N days"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        days = int(request.query_params.get('days', 30))
        today = date.today()
        future_date = today + timedelta(days=days)
        
        bills = Bill.objects.filter(
            user=request.user,
            is_active=True,
            is_paid=False,
            due_date__gte=today,
            due_date__lte=future_date
        ).order_by('due_date')
        
        upcoming_list = []
        for bill in bills:
            upcoming_list.append({
                'id': str(bill.id),
                'name': bill.name,
                'amount': str(bill.amount),
                'due_date': bill.due_date.isoformat(),
                'days_until_due': (bill.due_date - today).days,
                'category': bill.category,
                'frequency': bill.frequency,
                'reminder_days': bill.reminder_days
            })
        
        serializer = UpcomingBillSerializer(upcoming_list, many=True)
        return Response(serializer.data)


class MarkBillPaidView(APIView):
    """Mark a bill as paid"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, bill_id):
        try:
            bill = Bill.objects.get(id=bill_id, user=request.user)
            
            if bill.is_paid:
                return Response(
                    {"error": "Bill is already marked as paid"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            bill.is_paid = True
            bill.save()
            
            # Create payment record
            BillPayment.objects.create(
                bill=bill,
                amount=bill.amount,
                payment_method=request.data.get('payment_method', 'Unknown'),
                notes=request.data.get('notes', '')
            )
            
            AuditLog.objects.create(
                user=request.user,
                action='BILL_MARKED_PAID',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={'bill_id': str(bill.id)}
            )
            
            return Response(BillSerializer(bill).data)
        except Bill.DoesNotExist:
            return Response(
                {"error": "Bill not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class GenerateRecurringBillsView(APIView):
    """Generate upcoming recurring bills based on frequency"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Generate bills for the next N months based on recurring patterns"""
        months_ahead = int(request.data.get('months_ahead', 3))
        bill_ids = request.data.get('bill_ids', [])
        
        # Get recurring bills
        bills_query = Bill.objects.filter(
            user=request.user,
            is_recurring=True,
            is_active=True
        )
        
        if bill_ids:
            bills_query = bills_query.filter(id__in=bill_ids)
        
        bills = bills_query.all()
        generated_bills = []
        
        with transaction.atomic():
            for bill in bills:
                # Calculate next due date based on frequency
                current_due = bill.due_date
                
                # Generate bills for each month ahead
                for month_offset in range(1, months_ahead + 1):
                    if bill.frequency == 'MONTHLY':
                        next_due = self._add_months(current_due, month_offset)
                    elif bill.frequency == 'BIWEEKLY':
                        next_due = current_due + timedelta(days=14 * month_offset)
                    elif bill.frequency == 'WEEKLY':
                        next_due = current_due + timedelta(days=7 * month_offset)
                    elif bill.frequency == 'QUARTERLY':
                        next_due = self._add_months(current_due, month_offset * 3)
                    elif bill.frequency == 'SEMI_ANNUALLY':
                        next_due = self._add_months(current_due, month_offset * 6)
                    elif bill.frequency == 'ANNUALLY':
                        next_due = self._add_months(current_due, month_offset * 12)
                    else:
                        continue
                    
                    # Check if bill already exists for this date
                    existing = Bill.objects.filter(
                        user=request.user,
                        name=bill.name,
                        due_date=next_due,
                        is_active=True
                    ).exists()
                    
                    if not existing:
                        # Create new bill instance
                        new_bill = Bill.objects.create(
                            user=request.user,
                            name=bill.name,
                            amount=bill.amount,
                            due_date=next_due,
                            category=bill.category,
                            frequency=bill.frequency,
                            is_recurring=True,
                            reminder_days=bill.reminder_days,
                            notes=bill.notes,
                            is_paid=False,
                            is_active=True
                        )
                        generated_bills.append(new_bill)
            
            AuditLog.objects.create(
                user=request.user,
                action='RECURRING_BILLS_GENERATED',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={
                    'count': len(generated_bills),
                    'months_ahead': months_ahead
                }
            )
        
        serializer = BillSerializer(generated_bills, many=True)
        return Response({
            'generated_count': len(generated_bills),
            'bills': serializer.data
        })
    
    def _add_months(self, date, months):
        """Add months to a date, handling year rollover"""
        month = date.month - 1 + months
        year = date.year + month // 12
        month = month % 12 + 1
        day = min(date.day, [31, 29 if year % 4 == 0 and not (year % 100 == 0 and year % 400 != 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return date.replace(year=year, month=month, day=day)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class BillCalendarView(APIView):
    """Get bills organized by date for calendar view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        today = timezone.now().date()
        
        if not start_date or not end_date:
            # Default to current month
            start_date = today.replace(day=1)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        else:
            start_date = datetime.fromisoformat(start_date).date()
            end_date = datetime.fromisoformat(end_date).date()
        
        # Get bills in date range
        bills = Bill.objects.filter(
            user=request.user,
            is_active=True,
            due_date__gte=start_date,
            due_date__lte=end_date
        ).order_by('due_date', 'name')
        
        # Organize by date
        calendar_data = {}
        for bill in bills:
            date_key = bill.due_date.isoformat()
            if date_key not in calendar_data:
                calendar_data[date_key] = {
                    'date': date_key,
                    'total_amount': Decimal('0.00'),
                    'bills': []
                }
            
            calendar_data[date_key]['bills'].append({
                'id': str(bill.id),
                'name': bill.name,
                'amount': str(bill.amount),
                'category': bill.category,
                'is_paid': bill.is_paid,
                'frequency': bill.frequency
            })
            
            if not bill.is_paid:
                calendar_data[date_key]['total_amount'] += bill.amount
        
        # Convert to list and sort by date
        calendar_list = sorted(calendar_data.values(), key=lambda x: x['date'])
        
        return Response({
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days_with_bills': len(calendar_list),
            'calendar': calendar_list
        })
