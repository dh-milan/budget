import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, full_name, password=None, **extra_fields):
        """Create and return a regular user"""
        if not email:
            raise ValueError('Email is required')
        if not full_name:
            raise ValueError('Full name is required')
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            full_name=full_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, full_name, password=None, **extra_fields):
        """Create and return a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(email, full_name, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model using Google OAuth2 authentication.
    Username is replaced with Google Subject ID as the unique identifier.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=255)
    google_subject_id = models.CharField(max_length=255, unique=True, db_index=True)
    full_name = models.CharField(max_length=255)
    avatar_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    role = models.CharField(
        max_length=50,
        choices=[
            ('USER', 'User'),
            ('ADMIN', 'Admin'),
            ('SUPPORT', 'Support'),
        ],
        default='USER'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Override username field to use email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    # Custom manager
    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['google_subject_id']),
        ]
    
    def __str__(self):
        return self.email


class UserPreferences(models.Model):
    """User preferences and settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='preferences')
    currency = models.CharField(max_length=3, default='USD')
    dark_mode = models.BooleanField(default=True)
    biometrics_enabled = models.BooleanField(default=False)
    notification_email = models.BooleanField(default=True)
    notification_push = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_preferences'
    
    def __str__(self):
        return f"{self.user.email} preferences"


class AuditLog(models.Model):
    """Audit log for security and compliance"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.created_at}"


class LoginHistory(models.Model):
    """Track user login sessions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    login_time = models.DateTimeField(default=timezone.now)
    logout_time = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_info = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'login_history'
        ordering = ['-login_time']
    
    def __str__(self):
        return f"{self.user.email} - {self.login_time}"