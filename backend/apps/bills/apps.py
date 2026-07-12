from django.apps import AppConfig


class BillsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.bills'
    verbose_name = 'Bills'
    
    def ready(self):
        """Import signals when app is ready"""
        import apps.bills.signals  # noqa