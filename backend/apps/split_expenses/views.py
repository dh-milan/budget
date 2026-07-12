from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
from rest_framework.exceptions import PermissionDenied
from .models import ExpenseGroup, GroupMember, SplitExpense, ExpenseSplit, Settlement
from .serializers import (
    ExpenseGroupSerializer,
    GroupMemberSerializer,
    SplitExpenseSerializer,
    CreateSplitExpenseSerializer,
    SettlementSerializer,
    SettlementBalanceSerializer,
    GroupDashboardSerializer
)


class ExpenseGroupViewSet(viewsets.ModelViewSet):
    """ViewSet for managing expense groups"""
    serializer_class = ExpenseGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return expense groups where user is a member or creator"""
        user = self.request.user
        return ExpenseGroup.objects.filter(
            Q(created_by=user) | Q(members__user=user, members__is_active=True),
            is_active=True
        ).distinct()
    
    def perform_create(self, serializer):
        """Create expense group and add creator as member"""
        group = serializer.save(created_by=self.request.user)
        # Add creator as member
        GroupMember.objects.create(
            group=group,
            user=self.request.user
        )
    
    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Get group dashboard data"""
        group = self.get_object()
        
        # Get recent expenses
        recent_expenses = group.expenses.all()[:10]
        expense_serializer = SplitExpenseSerializer(recent_expenses, many=True)
        
        # Get pending settlements
        pending_settlements = group.settlements.filter(is_completed=False)
        settlement_serializer = SettlementSerializer(pending_settlements, many=True)
        
        # Calculate member balances
        members = group.members.filter(is_active=True)
        member_balances = []
        
        for member in members:
            # Calculate total paid
            total_paid = group.expenses.filter(
                paid_by=member.user
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
            
            # Calculate total share
            total_share = ExpenseSplit.objects.filter(
                expense__group=group,
                user=member.user
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Balance: positive = should receive, negative = should pay
            balance = total_paid - total_share
            
            member_balances.append({
                'user_id': member.user.id,
                'user_email': member.user.email,
                'user_name': member.user.get_full_name() or member.user.email,
                'total_paid': total_paid,
                'total_share': total_share,
                'balance': balance
            })
        
        # Calculate totals
        total_expenses = group.expenses.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')
        
        total_settlements = group.settlements.filter(
            is_completed=True
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        data = {
            'group': ExpenseGroupSerializer(group).data,
            'total_expenses': total_expenses,
            'total_settlements': total_settlements,
            'recent_expenses': expense_serializer.data,
            'pending_settlements': settlement_serializer.data,
            'member_balances': member_balances
        }
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to the group"""
        group = self.get_object()
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'Email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user by email
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already a member
        if GroupMember.objects.filter(group=group, user=user).exists():
            return Response(
                {'error': 'User is already a member'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create membership
        member = GroupMember.objects.create(
            group=group,
            user=user
        )
        
        serializer = GroupMemberSerializer(member)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def remove_member(self, request, pk=None):
        """Remove a member from the group"""
        group = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        member = get_object_or_404(
            GroupMember, 
            group=group, 
            user_id=user_id
        )
        
        # Don't allow removing the creator
        if member.user == group.created_by:
            return Response(
                {'error': 'Cannot remove group creator'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        member.is_active = False
        member.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class GroupMemberViewSet(viewsets.ModelViewSet):
    """ViewSet for managing group members"""
    serializer_class = GroupMemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return group members for groups user belongs to"""
        user = self.request.user
        return GroupMember.objects.filter(
            Q(group__created_by=user) | Q(user=user),
            is_active=True
        ).select_related('user', 'group')


class SplitExpenseViewSet(viewsets.ModelViewSet):
    """ViewSet for managing split expenses"""
    serializer_class = SplitExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return expenses for groups user belongs to"""
        user = self.request.user
        return SplitExpense.objects.filter(
            Q(group__created_by=user) | Q(group__members__user=user, group__members__is_active=True)
        ).distinct().select_related('group', 'paid_by')
    
    @action(detail=False, methods=['post'])
    def create_with_splits(self, request):
        """Create expense with automatic split calculation"""
        serializer = CreateSplitExpenseSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        group = get_object_or_404(ExpenseGroup, id=data['group_id'])
        
        # Check if user is a member
        is_member = GroupMember.objects.filter(
            group=group,
            user=request.user,
            is_active=True
        ).exists()
        
        if not is_member:
            return Response(
                {'error': 'You must be a group member to add expenses'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create expense
        expense = SplitExpense.objects.create(
            group=group,
            title=data['title'],
            total_amount=data['total_amount'],
            expense_type=data['expense_type'],
            category=data['category'],
            description=data.get('description', ''),
            expense_date=data['expense_date'],
            paid_by_id=data['paid_by_id'],
            receipt=data.get('receipt')
        )
        
        # Get active members
        members = GroupMember.objects.filter(group=group, is_active=True)
        
        # Calculate splits based on expense type
        if data['expense_type'] == 'EQUAL':
            # Equal split among all members
            split_amount = data['total_amount'] / len(members)
            for member in members:
                ExpenseSplit.objects.create(
                    expense=expense,
                    user=member.user,
                    amount=split_amount
                )
        
        elif data['expense_type'] == 'PERCENTAGE':
            # Equal percentage split (can be extended for custom percentages)
            split_amount = data['total_amount'] / len(members)
            for member in members:
                ExpenseSplit.objects.create(
                    expense=expense,
                    user=member.user,
                    amount=split_amount
                )
        
        elif data['expense_type'] == 'EXACT':
            # Exact amounts provided
            splits_data = data.get('splits', [])
            if not splits_data:
                return Response(
                    {'error': 'Splits data is required for EXACT type'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            for split_data in splits_data:
                ExpenseSplit.objects.create(
                    expense=expense,
                    user_id=split_data['user_id'],
                    amount=split_data['amount']
                )
        
        # Return the created expense
        expense_serializer = SplitExpenseSerializer(expense)
        return Response(expense_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark a split as paid"""
        expense = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        split = get_object_or_404(
            ExpenseSplit, 
            expense=expense, 
            user_id=user_id
        )
        
        split.is_paid = True
        split.paid_at = timezone.now()
        split.save()
        
        serializer = ExpenseSplitSerializer(split)
        return Response(serializer.data)


class SettlementViewSet(viewsets.ModelViewSet):
    """ViewSet for managing settlements"""
    serializer_class = SettlementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return settlements for groups user belongs to"""
        user = self.request.user
        return Settlement.objects.filter(
            Q(group__created_by=user) | Q(group__members__user=user, group__members__is_active=True)
        ).distinct()
    
    def perform_create(self, serializer):
        """Create settlement"""
        group_id = self.request.data.get('group_id')
        group = get_object_or_404(ExpenseGroup, id=group_id)
        
        # Check if user is a member
        is_member = GroupMember.objects.filter(
            group=group,
            user=self.request.user,
            is_active=True
        ).exists()
        
        if not is_member:
            raise PermissionDenied('You must be a group member to create settlements')
        
        serializer.save(group=group)
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark settlement as completed"""
        settlement = self.get_object()
        settlement.is_completed = True
        settlement.completed_at = timezone.now()
        settlement.save()
        
        serializer = self.get_serializer(settlement)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def balances(self, request):
        """Get settlement balances for all groups"""
        user = request.user
        group_id = request.query_params.get('group_id')
        
        # Get groups user belongs to
        groups = ExpenseGroup.objects.filter(
            Q(created_by=user) | Q(members__user=user, members__is_active=True),
            is_active=True
        ).distinct()
        
        if group_id:
            groups = groups.filter(id=group_id)
        
        # Calculate balances for each group
        balances = []
        for group in groups:
            members = group.members.filter(is_active=True)
            
            for member in members:
                # Calculate total paid
                total_paid = group.expenses.filter(
                    paid_by=member.user
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
                
                # Calculate total share
                total_share = ExpenseSplit.objects.filter(
                    expense__group=group,
                    user=member.user
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                
                # Balance
                balance = total_paid - total_share
                
                if balance != 0:  # Only include non-zero balances
                    balances.append({
                        'group_id': group.id,
                        'group_name': group.name,
                        'user_id': member.user.id,
                        'user_email': member.user.email,
                        'user_name': member.user.get_full_name() or member.user.email,
                        'total_paid': total_paid,
                        'total_share': total_share,
                        'balance': balance
                    })
        
        serializer = SettlementBalanceSerializer(balances, many=True)
        return Response(serializer.data)