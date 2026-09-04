from django import forms
from django.contrib.auth import get_user_model
from .models import Message
from mySpecialist.models import SpecialistPatientHistory

User = get_user_model()

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']

    def __init__(self, *args, **kwargs):
        self.sender = kwargs.pop('sender', None)
        super().__init__(*args, **kwargs)

        if not self.sender:
            self.fields['recipient'].queryset = User.objects.none()
            return

        # Pacjent może pisać do każdego specjalisty
        if self.sender.role == 'patient':
            self.fields['recipient'].queryset = User.objects.filter(role='specialist')

        # Specjalista może pisać tylko do swoich (obecnych i przeszłych) pacjentów
        elif self.sender.role == 'specialist':
            # Zbieramy ID pacjentów powiązanych z tym specjalistą
            patient_ids = SpecialistPatientHistory.objects.filter(
                specialist=self.sender
            ).values_list('patient_id', flat=True)

            self.fields['recipient'].queryset = User.objects.filter(id__in=patient_ids)

        else:
            self.fields['recipient'].queryset = User.objects.none()

    def save(self, commit=True):
        message = super().save(commit=False)
        message.sender = self.sender
        if commit:
            message.save()
        return message
