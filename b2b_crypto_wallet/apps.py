from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        """
        Method called when the app is ready.
        Imports signals to ensure they are registered.
        """
        import api.signals  # noqa: F401
