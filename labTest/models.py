from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class LabSurveyResult(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wyniki {self.patient} z dnia {self.date}"


class LabResultEntry(models.Model):
    VALUE_TYPES = [
        ('numeric', 'Wartość liczbowa'),
        ('text', 'Opis tekstowy'),
        ('choice', 'Wybór: pozytywny/negatywny'),
    ]

    survey = models.ForeignKey(LabSurveyResult, related_name='entries', on_delete=models.CASCADE)
    section = models.CharField(max_length=100, blank=True, null=True)
    test_name = models.CharField(max_length=100)
    value = models.CharField(max_length=100, blank=True, null=True)
    value_type = models.CharField(max_length=10, choices=VALUE_TYPES, default='numeric')
    unit = models.CharField(max_length=20, blank=True)
    reference_min = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    reference_max = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    def __str__(self):
        return f"{self.test_name}: {self.value or 'brak'} {self.unit}"

    def get_display_value(self):
        if self.value_type == 'choice':
            mapping = {
                'pozytywny': 'Pozytywny',
                'negatywny': 'Negatywny',
                '': 'Brak',
                None: 'Brak'
            }
            return mapping.get(self.value, 'Brak')
        return self.value or 'Brak'

    @property
    def is_out_of_range(self):
        if self.value_type != 'numeric' or not self.value:
            return False
        try:
            val = float(str(self.value).replace(',', '.'))
            if self.reference_min is None or self.reference_max is None:
                return False
            return val < float(self.reference_min) or val > float(self.reference_max)
        except (ValueError, TypeError):
            return False

    @property
    def is_in_range(self):
        if self.value_type != 'numeric' or not self.value:
            return False
        try:
            val = float(str(self.value).replace(',', '.'))
            if self.reference_min is None or self.reference_max is None:
                return False
            return self.reference_min <= val <= self.reference_max
        except (ValueError, TypeError):
            return False

    @property
    def is_positive(self):
        return self.value_type == 'choice' and self.value == 'pozytywny'

    @property
    def is_negative(self):
        return self.value_type == 'choice' and self.value == 'negatywny'
