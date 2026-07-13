from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Transaction
from datetime import datetime
import json

class SyncAPIView(APIView):
    """
    Offline Delta Sync API
    Handles batch updates from the mobile app's SyncWorker and returns server-side delta changes.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data
        
        last_sync_str = data.get('last_sync', '2000-01-01T00:00:00Z')
        last_sync = datetime.fromisoformat(last_sync_str.replace('Z', '+00:00'))

        client_updates = data.get('transactions', [])
        
        # 1. Apply client delta updates to the server database
        for tx_data in client_updates:
            remote_id = tx_data.get('remoteId')
            sync_status = tx_data.get('syncStatus')
            
            if sync_status == 'PENDING_UPDATE' and remote_id:
                try:
                    tx = Transaction.objects.get(id=remote_id, account__user=user)
                    tx.title = tx_data.get('title', tx.title)
                    tx.amount = tx_data.get('amount', tx.amount)
                    tx.save()
                except Transaction.DoesNotExist:
                    pass
                    
            elif sync_status == 'PENDING_DELETE' and remote_id:
                Transaction.objects.filter(id=remote_id, account__user=user).delete()
                
            elif sync_status == 'PENDING_INSERT':
                # Create new transaction (Simplified for demonstration)
                # account = Account.objects.get(user=user, ...)
                # Transaction.objects.create(account=account, title=tx_data['title'], ...)
                pass

        # 2. Fetch server-side changes that occurred AFTER the mobile app's last sync
        server_updates = Transaction.objects.filter(account__user=user, updated_at__gt=last_sync)
        
        # 3. Return the delta payload
        return Response({
            "status": "success",
            "last_sync": timezone.now().isoformat(),
            "server_updates": [
                {
                    "id": str(tx.id),
                    "title": tx.title,
                    "amount": str(tx.amount),
                    "updated_at": tx.updated_at.isoformat(),
                    "is_deleted": False # Example flag
                } for tx in server_updates
            ]
        })
