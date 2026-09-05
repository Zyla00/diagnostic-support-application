# predictions/services/aggregator.py
from typing import Dict, List, Any
from django.apps import apps
from django.utils import timezone

def _get_model_or_none(label: str):
    """Bezpieczne pobranie modelu po 'app_label.ModelName'."""
    try:
        return apps.get_model(label)
    except Exception:
        return None

# DOPASUJ te etykiety do swoich modeli:
SENT_Q_MODEL = _get_model_or_none("questionnaires.SentQuestionnaire") or _get_model_or_none("surveys.SentQuestionnaire")
LAB_RESULT_MODEL = _get_model_or_none("labTest.LabResult") or _get_model_or_none("labTest.LabTestResult")

def fetch_surveys(patient_id: int, ids: List[int]) -> List[Any]:
    if not SENT_Q_MODEL:
        return []
    return list(SENT_Q_MODEL.objects.filter(id__in=ids, patient_id=patient_id, is_filled=True))

def fetch_lab_results(patient_id: int, ids: List[int]) -> List[Any]:
    if not LAB_RESULT_MODEL:
        return []
    return list(LAB_RESULT_MODEL.objects.filter(id__in=ids, patient_id=patient_id))

def build_context_text(patient, surveys: List[Any], labs: List[Any]) -> str:
    """Tekst dla LLM/RAG z krótkim streszczeniem wejść."""
    lines = [f"Pacjent: {getattr(patient, 'get_full_name', lambda: str(patient))()}"]
    if surveys:
        lines.append("\n# Ankiety:")
        for s in surveys:
            name = getattr(getattr(s, "questionnaire", None), "name", "Ankieta")
            sent_at = getattr(s, "sent_at", None)
            filled_at = getattr(s, "filled_at", None)
            lines.append(f"- {name} (wysłano: {sent_at}, wypełniono: {filled_at})")
            # jeśli masz odpowiedzi w modelu (np. s.answers JSON)
            answers = getattr(s, "answers", None) or getattr(s, "response", None)
            if answers:
                lines.append(f"  Odpowiedzi: {answers}")
    if labs:
        lines.append("\n# Badania laboratoryjne:")
        for l in labs:
            name = getattr(l, "test_name", None) or getattr(l, "name", "Badanie")
            date = getattr(l, "collected_at", None) or getattr(l, "result_date", None)
            summary = getattr(l, "short_summary", None)
            lines.append(f"- {name} (data: {date}){f' — {summary}' if summary else ''}")
            values = getattr(l, "values", None) or getattr(l, "result_json", None)
            if values:
                lines.append(f"  Wartości: {values}")
    return "\n".join([str(x) for x in lines if x is not None])

def build_tabular_features(surveys: List[Any], labs: List[Any]) -> Dict[str, float]:
    """
    Przykładowy ekstraktor cech pod XGBoost/HerBERT.
    DOPASUJ pod swoje kolumny — tutaj tylko ilustracja.
    """
    features = {}
    # Przykład: policz liczbę wypełnionych ankiet i badań
    features["n_surveys"] = float(len(surveys))
    features["n_labs"] = float(len(labs))
    # TODO: rozbij 'labs' po konkretnych parametrach, np. 'CRP', 'HbA1c' itd.
    # if labs and hasattr(labs[0], "values"): ...
    return features
