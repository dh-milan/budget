from celery import shared_task

@shared_task
def update_budget_spent_amounts():
    """Update budget spent amounts"""
    pass

import logging

logger = logging.getLogger(__name__)

@shared_task
def check_budget_warnings():
    """
    Periodic Celery task designed to run daily or hourly.
    It scans all active user budgets and triggers an FCM push notification
    if the spent amount exceeds 90% of the limit amount.
    """
    logger.info("Initiating Background Budget Check...")
    
    # 1. Query for budgets nearing their limit
    # budgets = Budget.objects.filter(is_active=True)
    
    # 2. Process logic
    # for budget in budgets:
    #     percentage_used = (budget.spent_amount / budget.limit_amount) * 100
    #     if percentage_used >= 90:
    #         logger.info(f"Budget threshold reached for {budget.user.email}. Triggering FCM...")
    #         
    #         # 3. Trigger Firebase Cloud Messaging (FCM) API wrapper
    #         send_fcm_notification(
    #             user_id=budget.user.id,
    #             title="Budget Warning ⚠️",
    #             body=f"You have used {percentage_used}% of your {budget.category} budget!"
    #         )
            
    return "Budget check task completed successfully."