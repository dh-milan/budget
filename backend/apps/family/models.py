import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class FamilyGroup(models.Model):
    """Family groups for shared finances"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_families'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'family_groups'
        indexes = [
            models.Index(fields=['created_by']),
            models.Index(fields=['is_active']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.created_by.email}"


class FamilyMember(models.Model):
    """Family group members"""
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('MEMBER', 'Member'),
        ('CHILD', 'Child'),
        ('VIEWER', 'Viewer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey(
        FamilyGroup, 
        on_delete=models.CASCADE, 
        related_name='members'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='family_memberships'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='MEMBER')
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'family_members'
        indexes = [
            models.Index(fields=['family', 'role']),
            models.Index(fields=['family', 'is_active']),
        ]
        unique_together = ['family', 'user']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.family.name} - {self.user.email} ({self.role})"


class SharedBudget(models.Model):
    """Shared budgets for family groups"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey(
        FamilyGroup, 
        on_delete=models.CASCADE, 
        related_name='shared_budgets'
    )
    category = models.CharField(max_length=100)
    limit_amount = models.DecimalField(max_digits=15, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    month_start = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shared_budgets'
        indexes = [
            models.Index(fields=['family', 'month_start']),
            models.Index(fields=['family', 'category', 'month_start'], name='unique_shared_budget'),
        ]
        unique_together = ['family', 'category', 'month_start']
        ordering = ['-month_start', 'category']
    
    def __str__(self):
        return f"{self.family.name} - {self.category} - {self.month_start}"


class SharedGoal(models.Model):
    """Shared savings goals for families"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey(
        FamilyGroup, 
        on_delete=models.CASCADE, 
        related_name='shared_goals'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    target_amount = models.DecimalField(max_digits=15, decimal_places=2)
    current_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    target_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shared_goals'
        indexes = [
            models.Index(fields=['family', 'is_active']),
            models.Index(fields=['family', 'target_date']),
        ]
        ordering = ['-target_date', 'name']
    
    def __str__(self):
        return f"{self.family.name} - {self.name}"