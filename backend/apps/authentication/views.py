import os
import requests
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from .models import User, UserPreferences, AuditLog, LoginHistory
from .serializers import (
    UserSerializer, UserPreferencesSerializer, GoogleAuthSerializer
)


class GoogleAuthView(APIView):
    """
    Google OAuth2 authentication endpoint.
    Verifies Google ID token and returns JWT access/refresh tokens.
    """
    permission_classes = [permissions.AllowAny]

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

    def get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class LogoutView(APIView):
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

    def get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class UserProfileView(APIView):
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

    def get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


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


class CustomTokenRefreshView(TokenRefreshView):
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

    def get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class CustomTokenVerifyView(TokenVerifyView):
    """
    Custom token verify endpoint
    """
    permission_classes = [permissions.AllowAny]