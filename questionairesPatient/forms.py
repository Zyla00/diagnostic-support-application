from django import forms
from questionairesManager.models import Questionnaire
from django.db import models


class SendQuestionnaireForm(forms.Form):
    questionnaire = forms.ModelChoiceField(
        queryset=Questionnaire.objects.none(),
        label="Wybierz ankietę",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        specialist = kwargs.pop('specialist', None)
        super().__init__(*args, **kwargs)
        if specialist:
            self.fields['questionnaire'].queryset = Questionnaire.objects.filter(
                models.Q(is_global=True) | models.Q(owner=specialist)
            )
