from django.apps import AppConfig

# Loading signals on startup
class GameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'game'
    def ready(self):
        from . import signals  # noqa: F401