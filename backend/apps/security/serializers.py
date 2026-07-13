from rest_framework import serializers
from .models import TwoFactorAuth, Device, Session, SecurityLoginHistory, BiometricAuth


class TwoFactorAuthSerializer(serializers.ModelSerializer):
    """Serializer for 2FA settings"""
    qr_code_uri = serializers.SerializerMethodField()
    
    class Meta:
        model = TwoFactorAuth
        fields = [
            'id', 'is_enabled', 'backup_codes', 'last_used_at',
            'created_at', 'updated_at', 'qr_code_uri'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'secret_key': {'write_only': True}
        }
    
    def get_qr_code_uri(self, obj):
        """Get TOTP URI for QR code"""
        if obj.secret_key:
            return obj.get_totp_uri()
        return None


class TwoFactorSetupSerializer(serializers.Serializer):
    """Serializer for 2FA setup"""
    secret_key = serializers.CharField(read_only=True)
    qr_code_uri = serializers.CharField(read_only=True)
    backup_codes = serializers.ListField(read_only=True)


class TwoFactorVerifySerializer(serializers.Serializer):
    """Serializer for verifying 2FA token"""
    token = serializers.CharField(max_length=6, help_text="6-digit TOTP token")
    backup_code = serializers.CharField(
        max_length=20, 
        required=False, 
        help_text="Backup code (alternative to token)"
    )


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for devices"""
    class Meta:
        model = Device
        fields = [
            'id', 'device_type', 'device_name', 'device_id', 'push_token',
            'is_trusted', 'last_used_at', 'ip_address', 'user_agent',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'device_id': {'write_only': True}
        }


class SessionSerializer(serializers.ModelSerializer):
    """Serializer for sessions"""
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    device_type = serializers.CharField(source='device.device_type', read_only=True)
    is_current = serializers.SerializerMethodField()
    
    class Meta:
        model = Session
        fields = [
            'id', 'device', 'device_name', 'device_type', 'session_token',
            'ip_address', 'user_agent', 'location', 'is_active',
            'last_activity_at', 'expires_at', 'is_current', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'session_token': {'write_only': True}
        }
    
    def get_is_current(self, obj):
        """Check if this is the current session"""
        request = self.context.get('request')
        if request:
            # Get session token from request
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                return obj.session_token == token
        return False


class LoginHistorySerializer(serializers.ModelSerializer):
    """Serializer for login history"""
    class Meta:
        model = SecurityLoginHistory
        fields = [
            'id', 'status', 'ip_address', 'user_agent', 'location',
            'failure_reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BiometricAuthSerializer(serializers.ModelSerializer):
    """Serializer for biometric auth settings"""
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    
    class Meta:
        model = BiometricAuth
        fields = [
            'id', 'biometric_type', 'is_enabled', 'device', 'device_name',
            'last_used_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SecurityDashboardSerializer(serializers.Serializer):
    """Serializer for security dashboard"""
    two_factor_enabled = serializers.BooleanField()
    active_sessions = serializers.IntegerField()
    trusted_devices = serializers.IntegerField()
    recent_logins = LoginHistorySerializer(many=True)
    failed_login_attempts = serializers.IntegerField()
    last_login = LoginHistorySerializer()


class DeviceRegistrationSerializer(serializers.Serializer):
    """Serializer for device registration"""
    device_type = serializers.ChoiceField(choices=Device.DEVICE_TYPES)
    device_name = serializers.CharField(max_length=100)
    device_id = serializers.CharField(max_length=255)
    push_token = serializers.CharField(max_length=255, required=False)