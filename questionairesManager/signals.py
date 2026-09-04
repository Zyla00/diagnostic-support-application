from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model


User = get_user_model()

@receiver(post_save, sender=User)
def assign_global_questionnaires(sender, instance, created, **kwargs):
    if not created:
        return

    print(f"Utworzono konto: {instance}. Ankiety globalne dostępne automatycznie.")
