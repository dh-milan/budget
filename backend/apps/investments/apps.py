from django.apps import AppConfig


class InvestmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.investments'
    verbose_name = 'Investments'

    def ready(self):
        """Import signals when app is ready"""
        import apps.investments.signals  # noqa