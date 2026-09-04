# predictionModels/apps.py
from django.apps import AppConfig

class PredictionModelsConfig(AppConfig):  # <-- DUŻE "M"
    default_auto_field = "django.db.models.BigAutoField"
    name = "predictionModels"
    verbose_name = "Prediction Models"  # opcjonalnie
