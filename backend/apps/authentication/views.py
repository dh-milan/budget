import os
import requests
from django.conf import settings
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from .models import User, UserPreferences, AuditLog, LoginHistory
from .serializers import (
    UserSerializer, UserPreferencesSerializer, GoogleAuthSerializer
)
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings as django_settings


class ClientIPMixin:
    """Mixin to extract client IP address from request"""
    def get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class GoogleAuthView(ClientIPMixin, APIView):
    """
    Google OAuth2 authentication endpoint.
    Verifies Google ID token and returns JWT access/refresh tokens.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "ID token is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        token = serializer.validated_data['id_token']

        try:
            # Verify Google ID token cryptographically
            id_info = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            # Validate audience matches our client ID
            if id_info['aud'] != settings.GOOGLE_CLIENT_ID:
                raise ValueError('Invalid audience')

            # Extract user information from Google token
            google_subject_id = id_info['sub']
            email = id_info.get('email', '').lower()
            full_name = id_info.get('name', '')
            avatar_url = id_info.get('picture', '')
            email_verified = id_info.get('email_verified', False)

            if not email_verified:
                return Response(
                    {"error": "Email not verified with Google"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Find or create user
            user, created = User.objects.get_or_create(
                google_subject_id=google_subject_id,
                defaults={
                    'email': email,
                    'full_name': full_name,
                    'avatar_url': avatar_url,
                    'role': 'USER',
                    'is_active': True,
                }
            )

            # Update user info on subsequent logins
            if not created:
                user.full_name = full_name
                user.avatar_url = avatar_url
                user.save()

            # Create user preferences if they don't exist
            UserPreferences.objects.get_or_create(user=user)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            # Add custom claims to token
            access_token['email'] = user.email
            access_token['full_name'] = user.full_name
            access_token['role'] = user.role

            # Log successful authentication
            AuditLog.objects.create(
                user=user,
                action='GOOGLE_AUTH_SUCCESS',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={'created': created}
            )

            # Track login history
            LoginHistory.objects.create(
                user=user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                device_info={'user_agent': request.META.get('HTTP_USER_AGENT', '')}
            )

            return Response({
                "access": str(access_token),
                "refresh": str(refresh),
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "avatar_url": user.avatar_url,
                    "role": user.role,
                    "is_new_user": created,
                }
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {"error": f"Invalid Google token: {str(e)}"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {"error": f"Authentication failed: {str(e)}"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(ClientIPMixin, APIView):
    """
    Logout endpoint - blacklists the refresh token
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            # Log logout
            AuditLog.objects.create(
                user=request.user,
                action='USER_LOGOUT',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
            )

            # Update login history
            recent_login = LoginHistory.objects.filter(
                user=request.user, 
                logout_time__isnull=True
            ).first()
            if recent_login:
                recent_login.logout_time = timezone.now()
                recent_login.save()

            return Response(
                {"message": "Logout successful"}, 
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"Logout failed: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(ClientIPMixin, APIView):
    """
    Get and update current user profile
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        
        # Get or create preferences
        preferences, _ = UserPreferences.objects.get_or_create(user=user)
        preferences_serializer = UserPreferencesSerializer(preferences)
        
        return Response({
            'user': serializer.data,
            'preferences': preferences_serializer.data
        })

    def patch(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            
            AuditLog.objects.create(
                user=user,
                action='PROFILE_UPDATE',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
            )
            
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserPreferencesView(APIView):
    """
    Get and update user preferences
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        preferences, _ = UserPreferences.objects.get_or_create(user=request.user)
        serializer = UserPreferencesSerializer(preferences)
        return Response(serializer.data)

    def patch(self, request):
        preferences, _ = UserPreferences.objects.get_or_create(user=request.user)
        serializer = UserPreferencesSerializer(
            preferences, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenRefreshView(ClientIPMixin, TokenRefreshView):
    """
    Custom token refresh that logs the activity
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Log token refresh
            AuditLog.objects.create(
                user=request.user,
                action='TOKEN_REFRESH',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
            )
        
        return response


class CustomTokenVerifyView(TokenVerifyView):
    """
    Custom token verify endpoint
    """
    permission_classes = [permissions.AllowAny]


class PasswordResetRequestView(ClientIPMixin, APIView):
    """
    Request password reset email
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        from .serializers import PasswordResetRequestSerializer
        
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                
                # Generate password reset token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.id))
                
                # Build reset URL
                reset_url = f"{request.build_absolute_uri('/')[:-1]}/api/v1/auth/password-reset-confirm/{uid}/{token}/"
                
                # Send email
                subject = 'Password Reset Request - WealthFlow'
                message = render_to_string('emails/password_reset_email.txt', {
                    'user': user,
                    'reset_url': reset_url,
                })
                
                try:
                    send_mail(
                        subject,
                        message,
                        django_settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                    
                    # Log password reset request
                    AuditLog.objects.create(
                        user=user,
                        action='PASSWORD_RESET_REQUEST',
                        ip_address=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
                    )
                    
                    return Response({
                        "message": "Password reset email sent successfully"
                    }, status=status.HTTP_200_OK)
                except Exception as e:
                    return Response({
                        "error": "Failed to send email. Please try again later."
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except User.DoesNotExist:
                # Don't reveal that user doesn't exist
                pass
        
        # Always return success to prevent email enumeration
        return Response({
            "message": "If an account with that email exists, we've sent password reset instructions."
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(ClientIPMixin, APIView):
    """
    Confirm password reset with token
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request, uid, token):
        from .serializers import PasswordResetConfirmSerializer
        
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Decode user ID
                user_id = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(id=user_id)
                
                # Verify token
                if not default_token_generator.check_token(user, token):
                    return Response({
                        "error": "Invalid or expired password reset token"
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Set new password
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                
                # Blacklist all existing tokens for this user
                from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
                OutstandingToken.objects.filter(user=user).delete()
                
                # Log password reset
                AuditLog.objects.create(
                    user=user,
                    action='PASSWORD_RESET_COMPLETE',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
                )
                
                return Response({
                    "message": "Password reset successful. Please login with your new password."
                }, status=status.HTTP_200_OK)
                
            except (User.DoesNotExist, ValueError):
                return Response({
                    "error": "Invalid password reset link"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(ClientIPMixin, APIView):
    """
    Verify email address with token
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        try:
            # Decode and verify token
            from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
            
            serializer = URLSafeTimedSerializer(django_settings.SECRET_KEY)
            email = serializer.loads(token, salt='email-verification', max_age=86400)  # 24 hours
            
            # Mark user as verified
            user = User.objects.get(email=email)
            user.is_active = True  # Or add email_verified field
            user.save()
            
            # Log email verification
            AuditLog.objects.create(
                user=user,
                action='EMAIL_VERIFIED',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
            )
            
            return Response({
                "message": "Email verified successfully"
            }, status=status.HTTP_200_OK)
            
        except (User.DoesNotExist, BadSignature, SignatureExpired):
            return Response({
                "error": "Invalid or expired verification link"
            }, status=status.HTTP_400_BAD_REQUEST)


class EmailLoginView(ClientIPMixin, APIView):
    """
    Standard email/password login endpoint
    Returns JWT access and refresh tokens
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        email = request.data.get('email', '').lower().strip()
        password = request.data.get('password', '')

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate user
        user = authenticate(request, email=email, password=password)
        
        if user is None:
            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {"error": "Account is disabled"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        # Add custom claims to token
        access_token['email'] = user.email
        access_token['full_name'] = user.full_name
        access_token['role'] = user.role

        # Log successful authentication
        AuditLog.objects.create(
            user=user,
            action='EMAIL_LOGIN_SUCCESS',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
            payload={'method': 'email'}
        )

        # Track login history
        LoginHistory.objects.create(
            user=user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
            device_info={'user_agent': request.META.get('HTTP_USER_AGENT', '')}
        )

        return Response({
            "access": str(access_token),
            "refresh": str(refresh),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "role": user.role,
                "is_new_user": False,
            }
        }, status=status.HTTP_200_OK)


class RegisterView(ClientIPMixin, APIView):
    """
    User registration endpoint
    Creates a new user with email and password
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        email = request.data.get('email', '').lower().strip()
        password = request.data.get('password', '')
        full_name = request.data.get('name', '').strip()

        # Validation
        if not email or not password or not full_name:
            return Response(
                {"error": "Email, password, and full name are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(password) < 8:
            return Response(
                {"error": "Password must be at least 8 characters long"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "User with this email already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Create new user
            user = User.objects.create(
                email=email,
                full_name=full_name,
                google_subject_id=f"email_{email}",  # Placeholder for email users
                username=email.split('@')[0],  # Set username from email
                role='USER',
                is_active=True,
                password=make_password(password)  # Hash the password
            )

            # Create user preferences
            UserPreferences.objects.get_or_create(user=user)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            # Add custom claims to token
            access_token['email'] = user.email
            access_token['full_name'] = user.full_name
            access_token['role'] = user.role

            # Log registration
            AuditLog.objects.create(
                user=user,
                action='USER_REGISTRATION',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                payload={'method': 'email'}
            )

            return Response({
                "access": str(access_token),
                "refresh": str(refresh),
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "avatar_url": user.avatar_url,
                    "role": user.role,
                    "is_new_user": True,
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": f"Registration failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
