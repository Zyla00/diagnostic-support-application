from django.apps import AppConfig

INSTALLED_APPS = [
    'widget_tweaks',
]



class QuestionairesManagerConfig(AppConfig):
    #default_auto_field = 'django.db.models.BigAutoField'
    name = 'questionairesManager'

    def ready(self, instance=None):
        print(f"Nowy użytkownik: {instance}. Przypisuję globalne ankiety...")
        import questionairesManager.signals
