from django import forms
from django.db.models import Q
from .models import Recommendation
from questionairesManager.models import Questionnaire


class RecommendationForm(forms.ModelForm):
    class Meta:
        model = Recommendation
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Wpisz zalecenie...'
            })
        }
        labels = {
            'text': 'Nowe zalecenie'
        }


class SendQuestionnaireForm(forms.Form):
    questionnaire = forms.ModelChoiceField(
        queryset=Questionnaire.objects.none(),
        label="Wybierz ankietę",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, specialist=None, **kwargs):
        super().__init__(*args, **kwargs)
        if specialist:
            self.fields['questionnaire'].queryset = Questionnaire.objects.filter(
                Q(owner=specialist) | Q(is_global=True)
            ).filter(is_active=True).order_by('name')
