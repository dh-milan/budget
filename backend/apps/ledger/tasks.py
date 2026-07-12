from celery import shared_task

@shared_task
def categorize_transaction_task(transaction_id):
    """Auto-categorize a transaction using AI"""
    from apps.ledger.models import Transaction
    from apps.ai_copilot.services import GeminiCopilotService
    
    try:
        transaction = Transaction.objects.get(id=transaction_id)
        
        # Call AI to categorize
        predicted_category = GeminiCopilotService.categorize_transaction(
            title=transaction.title,
            amount=transaction.amount,
            note=transaction.note or ''
        )
        
        transaction.category = predicted_category
        transaction.save()
        
        return f"Categorized transaction {transaction_id} as {predicted_category}"
    except Transaction.DoesNotExist:
        return f"Transaction {transaction_id} not found"
    except Exception as e:
        raise categorize_transaction_task.retry(exc=e, countdown=60)