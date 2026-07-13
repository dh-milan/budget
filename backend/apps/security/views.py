from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import TwoFactorAuth, Device, Session, SecurityLoginHistory, BiometricAuth
from .serializers import (
    TwoFactorAuthSerializer,
    TwoFactorSetupSerializer,
    TwoFactorVerifySerializer,
    DeviceSerializer,
    SessionSerializer,
    LoginHistorySerializer,
    BiometricAuthSerializer,
    SecurityDashboardSerializer,
    DeviceRegistrationSerializer
)


class TwoFactorAuthViewSet(viewsets.ModelViewSet):
    """ViewSet for managing 2FA"""
    serializer_class = TwoFactorAuthSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's 2FA settings"""
        return TwoFactorAuth.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def setup(self, request):
        """Setup 2FA for user"""
        # Get or create 2FA settings
        two_factor, created = TwoFactorAuth.objects.get_or_create(
            user=request.user
        )
        
        # Generate secret key
        secret_key = two_factor.generate_secret_key()
        
        # Generate QR code URI
        qr_code_uri = two_factor.get_totp_uri()
        
        # Generate backup codes
        backup_codes = two_factor.generate_backup_codes()
        
        return Response({
            'secret_key': secret_key,
            'qr_code_uri': qr_code_uri,
            'backup_codes': backup_codes
        })
    
    @action(detail=False, methods=['post'])
    def verify(self, request):
        """Verify 2FA token"""
        serializer = TwoFactorVerifySerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        two_factor = get_object_or_404(TwoFactorAuth, user=request.user)
        
        # Verify token or backup code
        token = data.get('token')
        backup_code = data.get('backup_code')
        
        is_valid = False
        
        if token:
            is_valid = two_factor.verify_totp(token)
        elif backup_code:
            is_valid = two_factor.verify_backup_code(backup_code)
        
        if is_valid:
            two_factor.is_enabled = True
            two_factor.last_used_at = timezone.now()
            two_factor.save()
            
            return Response({'message': '2FA verified successfully'})
        else:
            return Response(
                {'error': 'Invalid token or backup code'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def disable(self, request):
        """Disable 2FA"""
        two_factor = get_object_or_404(TwoFactorAuth, user=request.user)
        
        # Require password confirmation or token
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'Token is required to disable 2FA'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if two_factor.verify_totp(token) or two_factor.verify_backup_code(token):
            two_factor.is_enabled = False
            two_factor.secret_key = ''
            two_factor.backup_codes = []
            two_factor.save()
            
            return Response({'message': '2FA disabled successfully'})
        else:
            return Response(
                {'error': 'Invalid token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def regenerate_backup_codes(self, request):
        """Regenerate backup codes"""
        two_factor = get_object_or_404(TwoFactorAuth, user=request.user)
        
        if not two_factor.is_enabled:
            return Response(
                {'error': '2FA is not enabled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Require token verification
        token = request.data.get('token')
        if not token or not two_factor.verify_totp(token):
            return Response(
                {'error': 'Valid token is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate new backup codes
        backup_codes = two_factor.generate_backup_codes()
        
        return Response({'backup_codes': backup_codes})


class DeviceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing devices"""
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's devices"""
        return Device.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Register device for current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def trust(self, request, pk=None):
        """Mark device as trusted"""
        device = self.get_object()
        device.is_trusted = True
        device.save()
        
        serializer = self.get_serializer(device)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def untrust(self, request, pk=None):
        """Mark device as untrusted"""
        device = self.get_object()
        device.is_trusted = False
        device.save()
        
        serializer = self.get_serializer(device)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_push_token(self, request, pk=None):
        """Update push notification token"""
        device = self.get_object()
        push_token = request.data.get('push_token')
        
        if not push_token:
            return Response(
                {'error': 'push_token is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        device.push_token = push_token
        device.last_used_at = timezone.now()
        device.save()
        
        serializer = self.get_serializer(device)
        return Response(serializer.data)


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing sessions"""
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's sessions"""
        return Session.objects.filter(
            user=self.request.user
        ).select_related('device')
    
    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        """Terminate a session"""
        session = self.get_object()
        
        # Don't allow terminating current session through this endpoint
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            if session.session_token == token:
                return Response(
                    {'error': 'Cannot terminate current session'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        session.is_active = False
        session.save()
        
        return Response({'message': 'Session terminated successfully'})
    
    @action(detail=False, methods=['post'])
    def terminate_all(self, request):
        """Terminate all sessions except current"""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        current_token = None
        
        if auth_header.startswith('Bearer '):
            current_token = auth_header[7:]
        
        # Terminate all other sessions
        sessions = Session.objects.filter(
            user=request.user,
            is_active=True
        ).exclude(session_token=current_token)
        
        count = sessions.count()
        sessions.update(is_active=False)
        
        return Response({
            'message': f'{count} sessions terminated successfully'
        })


class LoginHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing login history"""
    serializer_class = LoginHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's login history"""
        return SecurityLoginHistory.objects.filter(user=self.request.user)
    
    def list(self, request):
        """Get login history with pagination"""
        queryset = self.get_queryset()
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        queryset = queryset.filter(created_at__gte=start_date)
        
        # Get recent logins
        recent_logins = queryset[:100]
        serializer = self.get_serializer(recent_logins, many=True)
        
        # Get statistics
        total_attempts = queryset.count()
        failed_attempts = queryset.filter(status='FAILED').count()
        
        return Response({
            'total_attempts': total_attempts,
            'failed_attempts': failed_attempts,
            'results': serializer.data
        })


class BiometricAuthViewSet(viewsets.ModelViewSet):
    """ViewSet for managing biometric auth"""
    serializer_class = BiometricAuthSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's biometric auth settings"""
        return BiometricAuth.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def enable(self, request):
        """Enable biometric authentication"""
        biometric_type = request.data.get('biometric_type')
        device_id = request.data.get('device_id')
        
        if not biometric_type or not device_id:
            return Response(
                {'error': 'biometric_type and device_id are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get device
        device = get_object_or_404(Device, id=device_id, user=request.user)
        
        # Create or update biometric auth
        biometric, created = BiometricAuth.objects.get_or_create(
            user=request.user,
            defaults={'biometric_type': biometric_type}
        )
        
        biometric.biometric_type = biometric_type
        biometric.is_enabled = True
        biometric.device = device
        biometric.save()
        
        serializer = self.get_serializer(biometric)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def disable(self, request):
        """Disable biometric authentication"""
        biometric = get_object_or_404(BiometricAuth, user=request.user)
        biometric.is_enabled = False
        biometric.save()
        
        serializer = self.get_serializer(biometric)
        return Response(serializer.data)


class SecurityDashboardViewSet(viewsets.ViewSet):
    """ViewSet for security dashboard"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get security dashboard data"""
        user = request.user
        
        # Get 2FA status
        try:
            two_factor = TwoFactorAuth.objects.get(user=user)
            two_factor_enabled = two_factor.is_enabled
        except TwoFactorAuth.DoesNotExist:
            two_factor_enabled = False
        
        # Get active sessions
        active_sessions = Session.objects.filter(user=user, is_active=True).count()
        
        # Get trusted devices
        trusted_devices = Device.objects.filter(user=user, is_trusted=True).count()
        
        # Get recent logins (last 10)
        recent_logins = SecurityLoginHistory.objects.filter(user=user)[:10]
        recent_logins_serializer = LoginHistorySerializer(recent_logins, many=True)
        
        # Get failed login attempts (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        failed_login_attempts = SecurityLoginHistory.objects.filter(
            user=user,
            status='FAILED',
            created_at__gte=thirty_days_ago
        ).count()
        
        # Get last successful login
        last_login = SecurityLoginHistory.objects.filter(
            user=user,
            status='SUCCESS'
        ).first()
        last_login_serializer = LoginHistorySerializer(last_login) if last_login else None
        
        data = {
            'two_factor_enabled': two_factor_enabled,
            'active_sessions': active_sessions,
            'trusted_devices': trusted_devices,
            'recent_logins': recent_logins_serializer.data,
            'failed_login_attempts': failed_login_attempts,
            'last_login': last_login_serializer.data if last_login_serializer else None
        }
        
        serializer = SecurityDashboardSerializer(data)
        return Response(serializer.data)