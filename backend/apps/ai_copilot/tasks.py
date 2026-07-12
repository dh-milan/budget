from celery import shared_task

@shared_task
def generate_health_scores():
    """Generate health scores"""
    pass

@shared_task
def cleanup_old_logs():
    """Clean up old logs"""
    pass