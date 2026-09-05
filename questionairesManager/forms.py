from django import forms
from .models import Question, Section

class QuestionForm(forms.ModelForm):
    # Dodane: pole ID potrzebne dla modelformset
    id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    section = forms.ModelChoiceField(
        queryset=Section.objects.all(),  # Możesz filtrować po questionnaire, jeśli chcesz
        required=False,
        widget=forms.HiddenInput()
    )

    choices_text = forms.CharField(
        required=False,
        label="Opcje (jeśli wybór – podaj rozdzielone przecinkiem)",
        widget=forms.TextInput(attrs={
            'placeholder': 'np. Tak, Nie',
            'class': 'form-control'
        }),
    )

    class Meta:
        model = Question
        fields = ['id', 'question_text', 'question_type', 'section']
        widgets = {
            'question_text': forms.TextInput(attrs={'class': 'form-control'}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            # section i id są nadpisane wyżej jako ukryte
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk and self.instance.question_type in ['single_choice', 'multiple_choice']:
            self.fields['choices_text'].initial = ', '.join(
                c.text for c in self.instance.choices.all()
            )


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['name', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Np. Pytania tylko dla kobiet',
                'class': 'form-control'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
        }
        labels = {
            'name': 'Nazwa sekcji',
            'order': 'Kolejność'
        }
