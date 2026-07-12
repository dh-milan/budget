from celery import shared_task

@shared_task
def process_recurring_bills():
    """Process recurring bills"""
    pass

@shared_task
def check_bill_reminders():
    """Check bill reminders"""
    pass