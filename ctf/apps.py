from django.apps import AppConfig


class CtfConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ctf"

    def ready(self):
        from . import signals 
        signals.setup_initial_data(None) 