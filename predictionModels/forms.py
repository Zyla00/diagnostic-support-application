from django import forms
from .models import KnowledgeNote, TrainingJob

class KnowledgeNoteForm(forms.ModelForm):
    class Meta:
        model = KnowledgeNote
        fields = ["title", "text", "attachment"]

class RetrainForm(forms.ModelForm):
    class Meta:
        model = TrainingJob
        fields = ["model_name", "params"]
    model_name = forms.ChoiceField(choices=TrainingJob.MODEL_CHOICES)
    params = forms.JSONField(required=False, help_text="Opcjonalne hyperparametry w JSON.")
