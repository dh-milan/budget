import pyotp
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import io
import base64

class TOTPSetupView(APIView):
    """
    Generates a secure TOTP secret for the user and returns it as a Base32 string
    and a QR Code URI for Google Authenticator/Authy.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 1. Generate a secure random base32 secret
        secret = pyotp.random_base32()
        
        # Note: In a production app, save this secret to the UserProfile securely
        # request.user.profile.totp_secret = secret
        # request.user.profile.save()
        
        # 2. Generate the provisioning URI for standard Authenticator apps
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=request.user.email, 
            issuer_name="WealthFlow"
        )
        
        return Response({
            "secret": secret,
            "totp_uri": totp_uri,
            "message": "Use a library like qrcode.js on the frontend to render the totp_uri"
        })

class TOTPVerifyView(APIView):
    """
    Verifies a user-provided 6-digit TOTP token against their stored secret.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        token = request.data.get('token')
        secret = request.data.get('secret') # Typically loaded from request.user.profile.totp_secret
        
        if not token or not secret:
            return Response({"error": "Missing token or secret"}, status=400)
            
        totp = pyotp.TOTP(secret)
        
        # Verify the token against the current time window
        if totp.verify(token):
            # In production: Mark user session as 2FA-verified
            return Response({"status": "verified", "message": "2FA successfully authenticated."})
            
        return Response({"status": "invalid", "error": "Invalid or expired token."}, status=400)
