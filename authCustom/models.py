from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils import timezone


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('patient', 'Pacjent'),
        ('specialist', 'Specjalista'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')

    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(
            regex=r'^(\+?\d{9,15})$',
            message="Numer telefonu musi zawierać od 9 do 15 cyfr i może zaczynać się od '+'"
        )]
    )
    second_name = models.CharField(max_length=50, blank=True)

    def is_patient(self):
        return self.role == 'patient'

    def is_specialist(self):
        return self.role == 'specialist'

    def __str__(self):
        return self.get_full_name() or self.username



PESEL_VALIDATOR = RegexValidator(
    regex=r'^\d{11}$',
    message="PESEL musi zawierać dokładnie 11 cyfr."
)

PHONE_VALIDATOR = RegexValidator(
    regex=r'^(\+?\d{9,15})$',
    message="Numer telefonu musi zawierać od 9 do 15 cyfr i może zaczynać się od '+'"
)

PWZ_VALIDATOR = RegexValidator(
    regex=r'^\d{6,7}$',
    message="Numer PWZ powinien zawierać 6–7 cyfr."
)

INSURANCE_CHOICES = [
    ('NFZ', 'NFZ'),
    ('PRIVATE', 'Ubezpieczenie prywatne'),
    ('NONE', 'Brak ubezpieczenia'),
]

class PatientProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    birth_date = models.DateField(null=True, blank=True)
    pesel = models.CharField(
        max_length=11,
        blank=True,
        validators=[PESEL_VALIDATOR],
    )
    insurance = models.CharField(
        max_length=20,
        choices=INSURANCE_CHOICES,
        default='NFZ',
        blank=True
    )

    def __str__(self):
        return f"Pacjent: {self.user.get_full_name()}"

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)


class SpecialistProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    second_name = models.CharField(max_length=50, blank=True)
    photo = models.ImageField(upload_to="profile_photos/", null=True, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    education = models.CharField(max_length=255, blank=True)
    experience = models.TextField(blank=True)
    license_number = models.CharField(
        "Numer PWZ",
        max_length=7,
        blank=True,
        unique=True,
        validators=[PWZ_VALIDATOR],
    )
    location = models.CharField("Adres przyjęć", max_length=255, blank=True)
    description = models.TextField("Opis o mnie", blank=True)
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[PHONE_VALIDATOR],
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Lekarz: {self.user.get_full_name()} – {self.specialization}"

