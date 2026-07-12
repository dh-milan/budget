import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wealthflow.settings')

app = Celery('wealthflow')

# Load task configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Configure periodic tasks (Celery Beat)
app.conf.beat_schedule = {
    # Process recurring bills every midnight
    'process-recurring-bills-every-midnight': {
        'task': 'apps.bills.tasks.process_recurring_bills',
        'schedule': crontab(hour=0, minute=0),
    },
    
    # Generate AI financial health scores daily at 2 AM
    'generate-ai-health-scores-daily': {
        'task': 'apps.ai_copilot.tasks.generate_health_scores',
        'schedule': crontab(hour=2, minute=0),
    },
    
    # Check for upcoming bill reminders every hour
    'check-bill-reminders-hourly': {
        'task': 'apps.bills.tasks.check_bill_reminders',
        'schedule': crontab(minute=0),
    },
    
    # Clean up old AI usage logs weekly
    'cleanup-old-ai-logs-weekly': {
        'task': 'apps.ai_copilot.tasks.cleanup_old_logs',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),
    },
    
    # Update budget spent amounts daily
    'update-budget-spent-amounts-daily': {
        'task': 'apps.budgeting.tasks.update_budget_spent_amounts',
        'schedule': crontab(hour=1, minute=0),
    },
}


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')