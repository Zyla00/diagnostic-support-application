from django import forms
from labTest.models import LabSurveyResult
import logging


class LabSurveyResultForm(forms.ModelForm):
    class Meta:
        model = LabSurveyResult
        fields = ['date']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'dd.mm.rrrr'
            }),
        }


class LabResultEntryForm(forms.Form):
    section = forms.CharField(required=False, widget=forms.HiddenInput())

    test_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'readonly': 'readonly'
    }))

    value_type = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'readonly': 'readonly'
    }))

    unit = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'readonly': 'readonly'
    }))

    reference_min = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=4,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Brak'
        })
    )

    reference_max = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=4,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Brak'
        })
    )

    # Zawsze jako tekst, typ dynamicznie obsługiwany w clean()
    value = forms.CharField(required=False)

    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.debug(f'LabResultEntryForm INIT prefix: {self.prefix}, data: {self.data}')

        value_type = (
            self.data.get(self.add_prefix('value_type')) or
            self.initial.get('value_type') or
            'numeric'
        )

        # Zmieniamy tylko widget – nie typ pola!
        if value_type == 'numeric':
            self.fields['value'].widget = forms.NumberInput(attrs={'class': 'form-control'})
        elif value_type == 'text':
            self.fields['value'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
        elif value_type == 'choice':
            self.fields['value'] = forms.ChoiceField(
                required=False,
                choices=[
                    ('brak', 'Brak odpowiedzi'),
                    ('pozytywny', 'Pozytywny'),
                    ('negatywny', 'Negatywny')
                ],
                initial='brak',
                widget=forms.Select(attrs={'class': 'form-control'})
            )
        else:
            self.fields['value'].widget = forms.TextInput(attrs={'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        value = cleaned_data.get('value')
        value_type = cleaned_data.get('value_type')

        # Walidacja liczbowa z konwersją przecinka
        if value_type == 'numeric' and value not in [None, '']:
            try:
                float(value.replace(',', '.'))
            except (ValueError, TypeError):
                self.add_error('value', 'Wartość musi być liczbą.')

        if value_type == 'choice' and value not in ['pozytywny', 'negatywny', 'brak', None, '']:
            self.add_error('value', 'Wybierz opcję: pozytywny, negatywny lub brak.')

        return cleaned_data
