# models
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

# Agregatory / silniki (jak u Ciebie)
from .services.aggregator import (
    fetch_surveys,
    fetch_lab_results,
    build_context_text,
    build_tabular_features,
)
from .services.models import (
    xgboost_engine,
    herbert_engine,
    mistral_engine,
    mistral_rag_engine,
)

# relacja specjalista—pacjent
from mySpecialist.models import SpecialistPatientHistory

# dane do list
from questionairesPatient.models import SentQuestionnaireRequest
from labTest.models import LabSurveyResult, LabResultEntry

# orkiestrowanie retrainingu / RAG
from .service import (
    rag_add_note,
    rebuild_rag_index,
    retrain_herbert as retrain_herbert_service,
    retrain_xgboost as retrain_xgb_service,
    HERBERT_FINAL,
    HERBERT_DIR,
    XGB_DIR,
)

# AnalysisRun – opcjonalnie (żeby brak modelu nie wywalał)
try:
    from .models import AnalysisRun  # type: ignore
except Exception:
    AnalysisRun = None  # noqa: N816

User = get_user_model()


# ---------- helpers ----------

def _load_label_choices() -> list[str]:
    """Wczytaj klasy z label_encoder.json (HerBERT -> XGB) do podpowiedzi."""
    import json
    choices: list[str] = []
    try:
        p = HERBERT_FINAL / "label_encoder.json"
        if p.exists():
            with open(p, encoding="utf-8") as f:
                choices = list(json.load(f).get("classes", []))
        else:
            p2 = XGB_DIR / "final_model" / "label_encoder.json"
            if p2.exists():
                with open(p2, encoding="utf-8") as f:
                    choices = list(json.load(f).get("classes", []))
    except Exception:
        choices = []
    return sorted(choices)


def _fmt_dt(dt) -> Optional[str]:
    try:
        from django.utils.timezone import localtime
        return localtime(dt).strftime("%d.%m.%Y %H:%M")
    except Exception:
        return None


def _survey_to_text(s: SentQuestionnaireRequest) -> str:
    parts = [f"Ankieta: {getattr(getattr(s, 'questionnaire', None), 'name', '—')}"]
    if getattr(s, "filled_at", None):
        parts.append(f"Data wypełnienia: {_fmt_dt(s.filled_at)}")

    resp = getattr(s, "response", None)
    if resp:
        try:
            answers_qs = resp.answers.select_related("question").prefetch_related("selected_choices")
        except Exception:
            answers_qs = getattr(resp, "answers", [])
        for a in answers_qs:
            q = getattr(a, "question", None)
            qtext = (
                getattr(q, "text", None)
                or getattr(q, "title", None)
                or getattr(q, "label", None)
                or f"Pytanie {getattr(q, 'id', '')}"
            )
            qtype = getattr(q, "question_type", None)
            if qtype == "text":
                val = getattr(a, "text_answer", "") or getattr(a, "value", "")
            elif qtype == "single_choice":
                try:
                    ch = a.selected_choices.first()
                    val = getattr(ch, "text", "") if ch else ""
                except Exception:
                    val = ""
            elif qtype == "multiple_choice":
                try:
                    val = ", ".join([getattr(c, "text", "") for c in a.selected_choices.all()])
                except Exception:
                    val = ""
            else:
                val = getattr(a, "text_answer", "") or getattr(a, "value", "")
            if val not in (None, "", [], {}):
                parts.append(f"{qtext}: {val}")
    return "\n".join(parts)


def _lab_to_text(l: LabSurveyResult) -> str:
    parts = [f"Badanie: {getattr(l, 'name', str(l))}"]
    d = getattr(l, "collected_at", None) or getattr(l, "created_at", None)
    if d:
        parts.append(f"Data: {_fmt_dt(d)}")
    if getattr(l, "short_summary", None):
        parts.append(f"Podsumowanie: {l.short_summary}")

    try:
        entries = list(LabResultEntry.objects.filter(survey=l))[:15]
    except Exception:
        entries = []
    for e in entries:
        name = getattr(e, "test_name", None) or getattr(e, "name", None) or "Parametr"
        val = getattr(e, "value", None) or getattr(e, "result", None) or getattr(e, "result_value", None)
        unit = getattr(e, "unit", None)
        ref = getattr(e, "reference_range", None) or getattr(e, "ref", None)
        bits = [name]
        if val is not None:
            bits.append(str(val))
        if unit:
            bits.append(str(unit))
        if ref:
            bits.append(f"(ref: {ref})")
        parts.append(" - " + " ".join(bits))
    return "\n".join(parts)


def _user_can_access_patient(user, patient) -> bool:
    # Dostosuj do własnych reguł.
    return user.is_staff or user == patient or True


# ---------- budowa CSV: wiele przypadków ----------

def _build_training_csv_from_cases(
    *,
    cases: list[dict],
    dest_path: Path,
) -> Path:
    """
    Przyjmuje listę przypadków:
      { "survey_ids": [..], "lab_ids": [..], "label": "kardiolog", "case_text": "..." }
    Buduje CSV z kolumnami: Opis_przypadku, Alergie, Choroby_przewlekłe, Jednostka_medyczna.
    """
    import pandas as pd

    rows: list[dict] = []
    for idx, c in enumerate(cases, start=1):
        label = (c.get("label") or "").strip()
        case_text = (c.get("case_text") or "").strip()
        survey_ids = list(map(int, c.get("survey_ids") or []))
        lab_ids = list(map(int, c.get("lab_ids") or []))

        surveys = list(SentQuestionnaireRequest.objects.filter(id__in=survey_ids)) if survey_ids else []
        labs = list(LabSurveyResult.objects.filter(id__in=lab_ids)) if lab_ids else []

        blocks: list[str] = []
        if case_text:
            blocks.append(case_text)
        if surveys:
            blocks.extend(_survey_to_text(s) for s in surveys)
        if labs:
            blocks.extend(_lab_to_text(l) for l in labs)

        if not label:
            raise ValueError(f"Przypadek #{idx}: brak etykiety.")
        if not blocks:
            raise ValueError(f"Przypadek #{idx}: brak danych (wybierz ankiety/badania albo dodaj opis).")

        opis = "\n\n".join([t for t in blocks if t.strip()])
        rows.append({
            "Opis_przypadku": opis,
            "Alergie": "",
            "Choroby_przewlekłe": "",
            "Jednostka_medyczna": label,
        })

    if not rows:
        raise ValueError("Nie dodano żadnego przypadku.")

    df = pd.DataFrame(rows)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest_path, index=False, encoding="utf-8")
    return dest_path


# ---------- (opcjonalne) klasyczne run_analysis ----------

@login_required
@require_POST
def run_analysis(request: HttpRequest, patient_id: int):
    if AnalysisRun is None:
        return JsonResponse(
            {"ok": False, "error": "Brak modelu AnalysisRun w tej aplikacji."},
            status=400,
        )

    patient = get_object_or_404(User, pk=patient_id)
    if not _user_can_access_patient(request.user, patient):
        return JsonResponse({"ok": False, "error": "Brak uprawnień."}, status=403)

    if request.content_type == "application/json":
        payload = json.loads(request.body.decode("utf-8"))
        model_type = payload.get("model")
        survey_ids = payload.get("survey_ids") or []
        lab_ids = payload.get("lab_ids") or []
    else:
        model_type = request.POST.get("model")
        survey_ids = request.POST.getlist("survey_ids[]") or request.POST.getlist("survey_ids") or []
        lab_ids = request.POST.getlist("lab_ids[]") or request.POST.getlist("lab_ids") or []

    try:
        survey_ids = [int(x) for x in survey_ids]
        lab_ids = [int(x) for x in lab_ids]
    except Exception:
        return JsonResponse({"ok": False, "error": "Nieprawidłowe identyfikatory."}, status=400)

    if not model_type:
        return JsonResponse({"ok": False, "error": "Nie wybrano modelu."}, status=400)
    if not (survey_ids or lab_ids):
        return JsonResponse({"ok": False, "error": "Nie wybrano żadnych danych."}, status=400)

    surveys = fetch_surveys(patient.id, survey_ids)
    labs = fetch_lab_results(patient.id, lab_ids)

    run = AnalysisRun.objects.create(
        patient=patient,
        created_by=request.user,
        model_type=model_type,
        survey_ids=survey_ids,
        lab_result_ids=lab_ids,
        status="running",
        input_snapshot={
            "surveys": [getattr(getattr(s, "questionnaire", None), "name", f"survey:{s.pk}") for s in surveys],
            "labs": [getattr(l, "test_name", None) or getattr(l, "name", f"lab:{l.pk}") for l in labs],
        },
    )

    try:
        if model_type in (AnalysisRun.MODEL_XGBOOST, AnalysisRun.MODEL_HERBERT):
            features = build_tabular_features(surveys, labs)
            out = xgboost_engine.run(features) if model_type == AnalysisRun.MODEL_XGBOOST else herbert_engine.run(features)

            run.predicted_class = out.get("predicted_class")
            run.class_probs = out.get("class_probs")
            run.result = out
            run.status = "done"
            run.save()

            probs_list = [{"label": k, "prob": float(v)} for k, v in (run.class_probs or {}).items()]
            return JsonResponse({
                "ok": True,
                "run_id": run.id,
                "model": model_type,
                "predicted_class": run.predicted_class,
                "probs": probs_list,
                "raw": out.get("raw", {}),
            })

        elif model_type in (AnalysisRun.MODEL_MISTRAL, AnalysisRun.MODEL_MISTRAL_RAG):
            ctx = build_context_text(patient, surveys, labs)
            out = mistral_rag_engine.run(ctx) if model_type == AnalysisRun.MODEL_MISTRAL_RAG else mistral_engine.run(ctx)

            run.llm_confidence = out.get("llm_confidence")
            run.result = out
            run.status = "done"
            run.save()

            return JsonResponse({
                "ok": True,
                "run_id": run.id,
                "model": model_type,
                "summary": out.get("summary"),
                "llm_confidence": out.get("llm_confidence"),
                "extra_signals": out.get("extra_signals", []),
                "sources": out.get("sources", []),
                "raw": out.get("raw", {}),
            })

        else:
            run.status = "failed"
            run.save()
            return JsonResponse({"ok": False, "error": "Nieznany model."}, status=400)

    except Exception as e:
        run.status = "failed"
        run.result = {"error": str(e)}
        run.save()
        return JsonResponse({"ok": False, "error": f"Błąd analizy: {e}"}, status=500)


# ---------- ML Lab (listy) ----------

@login_required
def ml_lab(request: HttpRequest):
    user = request.user

    if getattr(user, "role", None) == "specialist":
        patient_ids = list(
            SpecialistPatientHistory.objects
            .filter(specialist=user, is_active=True)
            .values_list("patient_id", flat=True)
        )
        filled_surveys = (
            SentQuestionnaireRequest.objects
            .filter(patient_id__in=patient_ids)
            .select_related("patient", "questionnaire")
            .order_by("-sent_at")
        )
        lab_results = (
            LabSurveyResult.objects
            .filter(patient_id__in=patient_ids)
            .select_related("patient")
            .order_by("-created_at")
        )
    else:
        filled_surveys = (
            SentQuestionnaireRequest.objects
            .filter(patient=user)
            .select_related("patient", "questionnaire")
            .order_by("-sent_at")
        )
        lab_results = (
            LabSurveyResult.objects
            .filter(patient=user)
            .select_related("patient")
            .order_by("-created_at")
        )

    label_choices = _load_label_choices()

    return render(request, "predictions/ml_lab.html", {
        "filled_surveys": filled_surveys,
        "lab_results": lab_results,
        "label_choices": label_choices,
    })


# ---------- RAG: dodawanie notatek ----------

@login_required
@require_POST
def add_note_from_ui(request: HttpRequest):
    title = (request.POST.get("note_title") or "").strip()
    text = (request.POST.get("note_text") or "").strip()
    file = request.FILES.get("note_file")
    if not title or not text:
        messages.error(request, "Podaj tytuł i treść notatki.")
        return redirect("predictionModels:ml_lab")

    file_path = None
    if file:
        upload_dir = HERBERT_DIR.parent / "rag" / "notes_uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        fp = upload_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}_{file.name}"
        with open(fp, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)
        file_path = str(fp)

    try:
        messages.info(request, rag_add_note(title, text, file_path))
        msg = rebuild_rag_index()
        messages.success(request, msg)
    except Exception as e:
        messages.error(request, f"RAG – błąd dodawania notatki/indeksowania: {e}")
    return redirect("predictionModels:ml_lab")


# ---------- retraining: HerBERT / XGBoost (wiele przypadków) ----------

@login_required
@require_POST
def train_herbert_from_ui(request: HttpRequest):
    cases_raw = request.POST.get("h_cases_json", "[]").strip()
    try:
        cases = json.loads(cases_raw) if cases_raw else []
    except Exception as e:
        messages.error(request, f"Nieprawidłowy JSON przypadków (HerBERT): {e}")
        return redirect("predictionModels:ml_lab")

    # Walidacja – min. 1 case i min. 2 etykiety
    labels = { (c.get("label") or "").strip() for c in cases if (c.get("label") or "").strip() }
    if not cases:
        messages.error(request, "Dodaj przynajmniej jeden przypadek do zestawu (HerBERT).")
        return redirect("predictionModels:ml_lab")
    if len(labels) < 2:
        messages.error(request, "Do treningu potrzeba co najmniej 2 klasy (HerBERT). Dodaj przypadki z inną etykietą.")
        return redirect("predictionModels:ml_lab")

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    csv_path = HERBERT_DIR / f"finetune_{ts}.csv"
    try:
        _build_training_csv_from_cases(cases=cases, dest_path=csv_path)
    except Exception as e:
        messages.error(request, f"Nie udało się zbudować CSV (HerBERT): {e}")
        return redirect("predictionModels:ml_lab")

    try:
        msg = retrain_herbert_service({"csv_path": str(csv_path)})
    except Exception as e:
        messages.error(request, f"HerBERT – błąd treningu: {e}")
        return redirect("predictionModels:ml_lab")

    messages.success(request, msg)
    return redirect("predictionModels:ml_lab")


@login_required
@require_POST
def train_xgboost_from_ui(request: HttpRequest):
    cases_raw = request.POST.get("x_cases_json", "[]").strip()
    try:
        cases = json.loads(cases_raw) if cases_raw else []
    except Exception as e:
        messages.error(request, f"Nieprawidłowy JSON przypadków (XGBoost): {e}")
        return redirect("predictionModels:ml_lab")

    labels = { (c.get("label") or "").strip() for c in cases if (c.get("label") or "").strip() }
    if not cases:
        messages.error(request, "Dodaj przynajmniej jeden przypadek do zestawu (XGBoost).")
        return redirect("predictionModels:ml_lab")
    if len(labels) < 2:
        messages.error(request, "Do treningu potrzeba co najmniej 2 klasy (XGBoost). Dodaj przypadki z inną etykietą.")
        return redirect("predictionModels:ml_lab")

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    csv_path = XGB_DIR / f"retrain_{ts}.csv"
    try:
        _build_training_csv_from_cases(cases=cases, dest_path=csv_path)
    except Exception as e:
        messages.error(request, f"Nie udało się zbudować CSV (XGBoost): {e}")
        return redirect("predictionModels:ml_lab")

    try:
        msg = retrain_xgb_service({"csv_path": str(csv_path)})
    except Exception as e:
        messages.error(request, f"XGBoost – błąd treningu: {e}")
        return redirect("predictionModels:ml_lab")

    messages.success(request, msg)
    return redirect("predictionModels:ml_lab")
