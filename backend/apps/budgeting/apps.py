from django.apps import AppConfig


class BudgetingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.budgeting'
    verbose_name = 'Budgeting'
    
    def ready(self):
        """Import signals when app is ready"""
        import apps.budgeting.signals  # noqa