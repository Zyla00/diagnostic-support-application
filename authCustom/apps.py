from django.apps import AppConfig

class AuthCustomConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authCustom'

    def ready(self):
        import authCustom.signals

