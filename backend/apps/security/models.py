import uuid
import pyotp
import qrcode
from io import BytesIO
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile


class TwoFactorAuth(models.Model):
    """Two-factor authentication settings"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='two_factor_auth'
    )
    secret_key = models.CharField(max_length=255, help_text="TOTP secret key")
    is_enabled = models.BooleanField(default=False)
    backup_codes = models.JSONField(default=list, help_text="List of backup codes")
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'two_factor_auth'
        indexes = [
            models.Index(fields=['user', 'is_enabled']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - 2FA {'Enabled' if self.is_enabled else 'Disabled'}"
    
    def generate_secret_key(self):
        """Generate a new TOTP secret key"""
        self.secret_key = pyotp.random_base32()
        self.save()
        return self.secret_key
    
    def get_totp_uri(self):
        """Get the TOTP URI for QR code generation"""
        totp = pyotp.TOTP(self.secret_key)
        return totp.provisioning_uri(
            name=self.user.email,
            issuer_name="WealthFlow"
        )
    
    def generate_backup_codes(self, count=10):
        """Generate backup codes"""
        import secrets
        self.backup_codes = [secrets.token_hex(4) for _ in range(count)]
        self.save()
        return self.backup_codes
    
    def verify_totp(self, token):
        """Verify TOTP token"""
        totp = pyotp.TOTP(self.secret_key)
        return totp.verify(token)
    
    def verify_backup_code(self, code):
        """Verify and consume a backup code"""
        if code in self.backup_codes:
            self.backup_codes.remove(code)
            self.save()
            return True
        return False


class Device(models.Model):
    """User devices for trust management"""
    DEVICE_TYPES = [
        ('MOBILE', 'Mobile'),
        ('TABLET', 'Tablet'),
        ('DESKTOP', 'Desktop'),
        ('WEB', 'Web Browser'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='devices'
    )
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    device_name = models.CharField(max_length=100, help_text="User-friendly device name")
    device_id = models.CharField(max_length=255, help_text="Unique device identifier")
    push_token = models.CharField(max_length=255, blank=True, help_text="FCM/APNS token")
    is_trusted = models.BooleanField(default=False)
    last_used_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'devices'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['user', 'is_trusted']),
            models.Index(fields=['device_id']),
        ]
        unique_together = ['user', 'device_id']
        ordering = ['-last_used_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.device_name} ({self.device_type})"


class Session(models.Model):
    """User sessions for tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sessions'
    )
    device = models.ForeignKey(
        Device, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='sessions'
    )
    session_token = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    location = models.CharField(max_length=100, blank=True, help_text="City, Country")
    is_active = models.BooleanField(default=True)
    last_activity_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'sessions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_token']),
            models.Index(fields=['expires_at']),
        ]
        ordering = ['-last_activity_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.ip_address} - {self.created_at}"


class SecurityLoginHistory(models.Model):
    """Track login attempts and history for security purposes"""
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('2FA_REQUIRED', '2FA Required'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='security_login_history'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    location = models.CharField(max_length=100, blank=True)
    failure_reason = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'security_login_history'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['user', 'status']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.status} - {self.created_at}"


class BiometricAuth(models.Model):
    """Biometric authentication settings"""
    BIOMETRIC_TYPES = [
        ('FINGERPRINT', 'Fingerprint'),
        ('FACE', 'Face Recognition'),
        ('IRIS', 'Iris'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='biometric_auth'
    )
    biometric_type = models.CharField(max_length=20, choices=BIOMETRIC_TYPES)
    is_enabled = models.BooleanField(default=False)
    device = models.ForeignKey(
        Device, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='biometric_auth'
    )
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'biometric_auth'
        indexes = [
            models.Index(fields=['user', 'is_enabled']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.biometric_type} {'Enabled' if self.is_enabled else 'Disabled'}"