from django.apps import AppConfig


class SplitExpensesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.split_expenses'
    verbose_name = 'Split Expenses'

    def ready(self):
        """Import signals when app is ready"""
        import apps.split_expenses.signals  # noqa