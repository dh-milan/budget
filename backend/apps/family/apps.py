from django.apps import AppConfig


class FamilyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.family'
    verbose_name = 'Family Mode'

    def ready(self):
        """Import signals when app is ready"""
        import apps.family.signals  # noqa