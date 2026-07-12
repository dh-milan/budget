from celery import shared_task

@shared_task
def cleanup_old_login_history():
    """Clean up old login history"""
    from datetime import timedelta
    from django.utils import timezone
    from apps.authentication.models import LoginHistory
    
    cutoff_date = timezone.now() - timedelta(days=90)
    deleted_count, _ = LoginHistory.objects.filter(login_time__lt=cutoff_date).delete()
    return f"Deleted {deleted_count} old login history records"