from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .models import User, UserPreferences

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'avatar_url', 'role',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'role']


class UserPreferencesSerializer(serializers.ModelSerializer):
    """Serializer for UserPreferences model"""
    class Meta:
        model = UserPreferences
        fields = [
            'id', 'currency', 'date_format', 'theme',
            'notifications_enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GoogleAuthSerializer(serializers.Serializer):
    """Serializer for Google OAuth2 authentication"""
    id_token = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            # Don't reveal if email exists or not
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return attrs

    def validate_new_password(self, value):
        # Django's password validators will be applied automatically
        return value


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification"""
    token = serializers.CharField()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'full_name', 'password', 'password_confirm'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create(
            **validated_data,
            google_subject_id=f"email_{validated_data['email']}",
            role='USER',
            is_active=True  # Set to False if email verification is required
        )
        user.set_password(password)
        user.save()
        return user