from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, UserPreferences, AuditLog, LoginHistory


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'avatar_url', 
            'is_active', 'role', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserPreferencesSerializer(serializers.ModelSerializer):
    """Serializer for UserPreferences"""
    class Meta:
        model = UserPreferences
        fields = [
            'currency', 'dark_mode', 'biometrics_enabled',
            'notification_email', 'notification_push', 'updated_at'
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user_email', 'action', 'ip_address', 'payload', 'created_at']
        read_only_fields = fields


class LoginHistorySerializer(serializers.ModelSerializer):
    """Serializer for LoginHistory"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = LoginHistory
        fields = [
            'id', 'user_email', 'login_time', 'logout_time',
            'ip_address', 'device_info'
        ]
        read_only_fields = fields


class GoogleAuthSerializer(serializers.Serializer):
    """Serializer for Google OAuth2 authentication"""
    id_token = serializers.CharField(required=True, help_text="Google ID Token from client")


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with additional user data"""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['email'] = user.email
        token['full_name'] = user.full_name
        token['role'] = user.role
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'full_name': self.user.full_name,
            'avatar_url': self.user.avatar_url,
            'role': self.user.role,
        }
        return data


class TokenRefreshSerializer(serializers.Serializer):
    """Serializer for token refresh"""
    refresh = serializers.CharField(required=True)


class TokenVerifySerializer(serializers.Serializer):
    """Serializer for token verification"""
    token = serializers.CharField(required=True)