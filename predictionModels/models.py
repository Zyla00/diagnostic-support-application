from django.conf import settings
from django.db import models

# class AnalysisRun(models.Model):
#     MODEL_MISTRAL = "mistral"
#     MODEL_MISTRAL_RAG = "mistral_rag"
#     MODEL_XGBOOST = "xgboost"
#     MODEL_HERBERT = "herbert"
#
#     MODEL_CHOICES = [
#         (MODEL_MISTRAL, "Mistral"),
#         (MODEL_MISTRAL_RAG, "Mistral (RAG)"),
#         (MODEL_XGBOOST, "XGBoost"),
#         (MODEL_HERBERT, "HerBERT"),
#     ]
#
#     STATUS_CHOICES = [
#         ("queued", "Queued"),
#         ("running", "Running"),
#         ("done", "Done"),
#         ("failed", "Failed"),
#     ]
#
#     patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="analysis_runs")
#     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_analysis_runs")
#     model_type = models.CharField(max_length=32, choices=MODEL_CHOICES)
#     status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="running")
#
#     # Przechowujemy identyfikatory wybranych ankiet i wyników — bez twardych FK do Twoich aplikacji
#     survey_ids = models.JSONField(default=list, blank=True)
#     lab_result_ids = models.JSONField(default=list, blank=True)
#
#     # Zrzuty wejścia/wyjścia
#     input_snapshot = models.JSONField(null=True, blank=True)
#     result = models.JSONField(null=True, blank=True)
#
#     # Pola pomocnicze pod klasyfikację
#     predicted_class = models.CharField(max_length=128, null=True, blank=True)
#     class_probs = models.JSONField(null=True, blank=True)  # np. {"neg":0.12,"pos":0.88}
#     llm_confidence = models.FloatField(null=True, blank=True)  # 0..1 (heurystyka)
#
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"{self.get_model_type_display()} / {self.patient} / {self.created_at:%Y-%m-%d %H:%M}"
#

from django.db import models
from django.contrib.postgres.fields import JSONField  # jeśli nie używasz PSQL, zamień na models.JSONField

class KnowledgeNote(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField()
    # opcjonalne pole na plik źródłowy (pdf, docx, csv itp.)
    attachment = models.FileField(upload_to="rag_notes/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class TrainingJob(models.Model):
    MODEL_CHOICES = [
        ("herbert", "HerBERT (finetune)"),
        ("xgboost", "XGBoost (retrain)"),
        ("rag_index", "RAG (rebuild index)"),
    ]
    model_name = models.CharField(max_length=50, choices=MODEL_CHOICES)
    params = models.JSONField(blank=True, null=True)  # w razie potrzeby podaj hyperparametry
    status = models.CharField(max_length=30, default="queued")  # queued|running|succeeded|failed
    log = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_model_name_display()} ({self.status})"
