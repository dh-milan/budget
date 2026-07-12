from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q
from rest_framework.exceptions import PermissionDenied
from .models import FamilyGroup, FamilyMember, SharedBudget, SharedGoal
from .serializers import (
    FamilyGroupSerializer,
    FamilyMemberSerializer,
    SharedBudgetSerializer,
    SharedGoalSerializer,
    FamilyDashboardSerializer
)


class FamilyGroupViewSet(viewsets.ModelViewSet):
    """ViewSet for managing family groups"""
    serializer_class = FamilyGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return family groups where user is a member"""
        user = self.request.user
        return FamilyGroup.objects.filter(
            Q(created_by=user) | Q(members__user=user, members__is_active=True),
            is_active=True
        ).distinct()
    
    def perform_create(self, serializer):
        """Create family group and add creator as admin"""
        family = serializer.save(created_by=self.request.user)
        # Add creator as admin member
        FamilyMember.objects.create(
            family=family,
            user=self.request.user,
            role='ADMIN'
        )
    
    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Get family dashboard data"""
        family = self.get_object()
        
        # Get active members
        members = family.members.filter(is_active=True)
        member_serializer = FamilyMemberSerializer(members, many=True)
        
        # Get active budgets
        from datetime import date
        current_month = date.today().replace(day=1)
        budgets = family.shared_budgets.filter(
            is_active=True,
            month_start=current_month
        )
        budget_serializer = SharedBudgetSerializer(budgets, many=True)
        
        # Get active goals
        goals = family.shared_goals.filter(is_active=True)
        goal_serializer = SharedGoalSerializer(goals, many=True)
        
        # Calculate totals
        total_budget_spent = sum(budget.spent_amount for budget in budgets)
        total_goal_progress = sum(goal.current_amount for goal in goals)
        
        data = {
            'family': FamilyGroupSerializer(family).data,
            'total_members': members.count(),
            'active_budgets': budget_serializer.data,
            'active_goals': goal_serializer.data,
            'total_budget_spent': total_budget_spent,
            'total_goal_progress': total_goal_progress
        }
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def invite_member(self, request, pk=None):
        """Invite a new member to the family"""
        family = self.get_object()
        email = request.data.get('email')
        role = request.data.get('role', 'MEMBER')
        
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
        if FamilyMember.objects.filter(family=family, user=user).exists():
            return Response(
                {'error': 'User is already a member'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create membership
        member = FamilyMember.objects.create(
            family=family,
            user=user,
            role=role
        )
        
        serializer = FamilyMemberSerializer(member)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def remove_member(self, request, pk=None):
        """Remove a member from the family"""
        family = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        member = get_object_or_404(
            FamilyMember, 
            family=family, 
            user_id=user_id
        )
        
        # Don't allow removing the creator
        if member.user == family.created_by:
            return Response(
                {'error': 'Cannot remove family creator'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        member.is_active = False
        member.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class FamilyMemberViewSet(viewsets.ModelViewSet):
    """ViewSet for managing family members"""
    serializer_class = FamilyMemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return family members for families user belongs to"""
        user = self.request.user
        return FamilyMember.objects.filter(
            Q(family__created_by=user) | Q(user=user),
            is_active=True
        ).select_related('user', 'family')
    
    @action(detail=True, methods=['post'])
    def change_role(self, request, pk=None):
        """Change member role"""
        member = self.get_object()
        new_role = request.data.get('role')
        
        if new_role not in ['ADMIN', 'MEMBER', 'CHILD', 'VIEWER']:
            return Response(
                {'error': 'Invalid role'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        member.role = new_role
        member.save()
        
        serializer = self.get_serializer(member)
        return Response(serializer.data)


class SharedBudgetViewSet(viewsets.ModelViewSet):
    """ViewSet for managing shared budgets"""
    serializer_class = SharedBudgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return shared budgets for families user belongs to"""
        user = self.request.user
        return SharedBudget.objects.filter(
            Q(family__created_by=user) | Q(family__members__user=user, family__members__is_active=True),
            is_active=True
        ).distinct()
    
    def perform_create(self, serializer):
        """Create shared budget"""
        family_id = self.request.data.get('family_id')
        family = get_object_or_404(FamilyGroup, id=family_id)
        
        # Check if user is admin
        is_admin = FamilyMember.objects.filter(
            family=family,
            user=self.request.user,
            role='ADMIN'
        ).exists()
        
        if not is_admin and family.created_by != self.request.user:
            raise PermissionDenied('Only admins can create budgets')
        
        serializer.save(family=family)


class SharedGoalViewSet(viewsets.ModelViewSet):
    """ViewSet for managing shared goals"""
    serializer_class = SharedGoalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return shared goals for families user belongs to"""
        user = self.request.user
        return SharedGoal.objects.filter(
            Q(family__created_by=user) | Q(family__members__user=user, family__members__is_active=True),
            is_active=True
        ).distinct()
    
    def perform_create(self, serializer):
        """Create shared goal"""
        family_id = self.request.data.get('family_id')
        family = get_object_or_404(FamilyGroup, id=family_id)
        
        # Check if user is a member
        is_member = FamilyMember.objects.filter(
            family=family,
            user=self.request.user,
            is_active=True
        ).exists()
        
        if not is_member:
            raise PermissionDenied('You must be a family member to create goals')
        
        serializer.save(family=family)
    
    @action(detail=True, methods=['post'])
    def contribute(self, request, pk=None):
        """Add contribution to shared goal"""
        goal = self.get_object()
        amount = request.data.get('amount')
        
        if not amount or float(amount) <= 0:
            return Response(
                {'error': 'Valid amount is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is a member
        is_member = FamilyMember.objects.filter(
            family=goal.family,
            user=request.user,
            is_active=True
        ).exists()
        
        if not is_member:
            return Response(
                {'error': 'You must be a family member to contribute'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update goal
        goal.current_amount += float(amount)
        
        # Check if goal is completed
        if goal.current_amount >= goal.target_amount:
            goal.is_completed = True
        
        goal.save()
        
        serializer = self.get_serializer(goal)
        return Response(serializer.data)