from django.db import models
from django.conf import settings
from questionairesManager.models import Questionnaire

class UserSpecialist(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="my_specialist"
    )
    specialist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patients"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} -> {self.specialist}"


class SpecialistPatientHistory(models.Model):
    specialist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_history',
        limit_choices_to={'role': 'specialist'}
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='specialist_history',
        limit_choices_to={'role': 'patient'}
    )
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    resigned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('specialist', 'patient')
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.patient.get_full_name()} → {self.specialist.get_full_name()}"


class Recommendation(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    specialist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommendations'
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Zalecenie dla {self.patient.get_full_name()} ({self.created_at.strftime('%d.%m.%Y')})"


class SentQuestionnaireRequest(models.Model):
    questionnaire = models.ForeignKey(
        Questionnaire,
        on_delete=models.CASCADE,
        related_name='sent_requests_from_specialist'
    )
    specialist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_questionnaires'
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_questionnaires'
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    is_filled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.questionnaire.name} → {self.patient.get_full_name()}"


class AnalysisRun(models.Model):
    MODEL_MISTRAL = "mistral"
    MODEL_MISTRAL_RAG = "mistral_rag"
    MODEL_XGBOOST = "xgboost"
    MODEL_HERBERT = "herbert"

    MODEL_CHOICES = [
        (MODEL_MISTRAL, "Mistral"),
        (MODEL_MISTRAL_RAG, "Mistral (RAG)"),
        (MODEL_XGBOOST, "XGBoost"),
        (MODEL_HERBERT, "HerBERT"),
    ]

    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("running", "Running"),
        ("done", "Done"),
        ("failed", "Failed"),
    ]

    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="analysis_runs")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_analysis_runs")
    model_type = models.CharField(max_length=32, choices=MODEL_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="running")

    # Przechowujemy identyfikatory wybranych ankiet i wyników — bez twardych FK do Twoich aplikacji
    survey_ids = models.JSONField(default=list, blank=True)
    lab_result_ids = models.JSONField(default=list, blank=True)

    # Zrzuty wejścia/wyjścia
    input_snapshot = models.JSONField(null=True, blank=True)
    result = models.JSONField(null=True, blank=True)

    # Pola pomocnicze pod klasyfikację
    predicted_class = models.CharField(max_length=128, null=True, blank=True)
    class_probs = models.JSONField(null=True, blank=True)  # np. {"neg":0.12,"pos":0.88}
    llm_confidence = models.FloatField(null=True, blank=True)  # 0..1 (heurystyka)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_model_type_display()} / {self.patient} / {self.created_at:%Y-%m-%d %H:%M}"
