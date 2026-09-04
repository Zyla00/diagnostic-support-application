from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import PatientProfile, SpecialistProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'patient':
            PatientProfile.objects.get_or_create(user=instance)
        elif instance.role == 'specialist':
            SpecialistProfile.objects.get_or_create(user=instance)
