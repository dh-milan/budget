from django.apps import AppConfig


class LedgerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ledger'
    verbose_name = 'Ledger'
    
    def ready(self):
        """Import signals when app is ready"""
        import apps.ledger.signals  # noqa