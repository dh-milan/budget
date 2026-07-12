from django.apps import AppConfig


class AICopilotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai_copilot'
    verbose_name = 'AI Copilot'
    
    def ready(self):
        """Import signals when app is ready"""
        import apps.ai_copilot.signals  # noqa