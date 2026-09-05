from collections import OrderedDict
from itertools import groupby
from operator import attrgetter
from predictionModels.services.models.mistral_engine import generate_text
from predictionModels.services.models.mistral_rag_engine import generate_with_rag
from predictionModels.services.models.herbert_engine import predict_from_surveys as herbert_predict

import json
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localtime
from django.urls import reverse
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_GET
from django.template.loader import render_to_string
from predictionModels.services.models.xgboost_engine import (
    predict_from_surveys_and_labs as xgb_predict,
)


from labTest.models import LabSurveyResult, LabResultEntry
from labTest.views import get_default_lab_tests
from .models import UserSpecialist, SpecialistPatientHistory, Recommendation
from .forms import RecommendationForm, SendQuestionnaireForm
from questionairesManager.models import Questionnaire
from questionairesPatient.models import SentQuestionnaireRequest

User = get_user_model()


@login_required
def specialist_list(request):
    query = request.GET.get('q', '')
    specialists = User.objects.filter(role='specialist').select_related('specialistprofile')

    if query:
        specialists = specialists.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    my_specialist = None
    if hasattr(request.user, 'my_specialist'):
        my_specialist = request.user.my_specialist.specialist
        specialists = specialists.exclude(id=my_specialist.id)

    paginator = Paginator(specialists, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'specialists/list.html', {
        'page_obj': page_obj,
        'my_specialist': my_specialist,
        'query': query,
    })


@login_required
def choose_specialist(request, specialist_id):
    specialist = get_object_or_404(User, id=specialist_id, role='specialist')

    if hasattr(request.user, 'my_specialist'):
        request.user.my_specialist.delete()

    history, created = SpecialistPatientHistory.objects.get_or_create(
        specialist=specialist,
        patient=request.user,
        defaults={'is_active': True}
    )
    if not created:
        history.is_active = True
        history.resigned_at = None
        history.save()

    UserSpecialist.objects.update_or_create(user=request.user, defaults={'specialist': specialist})
    messages.success(request, "Pomyślnie wybrano specjalistę.")
    return redirect('specialist_list')


@login_required
def resign_specialist(request):
    if hasattr(request.user, 'my_specialist'):
        specialist = request.user.my_specialist.specialist
        request.user.my_specialist.delete()

        try:
            history = SpecialistPatientHistory.objects.get(specialist=specialist, patient=request.user)
            history.is_active = False
            history.resigned_at = timezone.now()
            history.save()
        except SpecialistPatientHistory.DoesNotExist:
            pass

        messages.warning(request, "Zrezygnowano z leczenia u specjalisty.")
    return redirect('specialist_list')


@login_required
def my_patients(request):
    if request.user.role != 'specialist':
        return redirect('dashboard')

    query = request.GET.get('q', '')
    history = SpecialistPatientHistory.objects.filter(specialist=request.user).select_related('patient')

    if query:
        history = history.filter(
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query)
        )

    paginator = Paginator(history, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'specialists/my_patients.html', {
        'page_obj': page_obj,
        'query': query,
    })

from django.core.paginator import Paginator
from labTest.models import LabSurveyResult
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(User, id=patient_id, role='patient')
    profile = getattr(patient, 'patientprofile', None)

    if request.method == 'POST' and 'text' in request.POST:
        form = RecommendationForm(request.POST)
        if form.is_valid():
            rec = form.save(commit=False)
            rec.specialist = request.user
            rec.patient = patient
            rec.save()
            return redirect('patient_detail', patient_id=patient.id)
    else:
        form = RecommendationForm()

    # Rekomendacje
    recommendations_queryset = Recommendation.objects.filter(patient=patient).order_by('-created_at')
    rec_paginator = Paginator(recommendations_queryset, 5)
    rec_page_number = request.GET.get('rec_page')
    recommendations = rec_paginator.get_page(rec_page_number)

    # Ankiety
    send_form = SendQuestionnaireForm(specialist=request.user)
    sent_queryset = SentQuestionnaireRequest.objects.filter(
        patient=patient
    ).select_related('questionnaire').order_by('-sent_at')
    paginator = Paginator(sent_queryset, 5)
    page_number = request.GET.get('sent_page')
    sent_history = paginator.get_page(page_number)

    # 🧪 Badania laboratoryjne
    survey_qs = LabSurveyResult.objects.filter(patient=patient).order_by('-created_at')
    survey_paginator = Paginator(survey_qs, 5)
    survey_page_number = request.GET.get('lab_page')
    surveys = survey_paginator.get_page(survey_page_number)

    filled_surveys = sent_queryset
    lab_results = survey_qs

    return render(request, 'specialists/patient_detail.html', {
        'patient': patient,
        'profile': profile,
        'recommendations': recommendations,
        'form': form,
        'send_form': send_form,
        'sent_history': sent_history,
        'surveys': surveys,
        'filled_surveys': filled_surveys,
        'lab_results': lab_results,
    })


@login_required
def my_recommendations(request):
    if request.user.role != 'patient':
        return redirect('patient_dashboard')

    # Zaznacz nieprzeczytane jako przeczytane
    unread_recs = Recommendation.objects.filter(patient=request.user, is_read=False)
    unread_recs.update(is_read=True)

    # Paginacja
    recommendations_queryset = Recommendation.objects.filter(
        patient=request.user
    ).select_related('specialist').order_by('-created_at')

    paginator = Paginator(recommendations_queryset, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'myPatient/recommendations.html', {
        'page_obj': page_obj,
        'current_page': 'recommendations',
    })



@login_required
def questionnaire_preview_or_answers(request, questionnaire_id):
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    sections = questionnaire.sections.prefetch_related(
        'questions__choices'
    ).all()

    return render(request, 'questionnairesPatient/questionnaire_preview.html', {
        'questionnaire': questionnaire,
        'sections': sections,
    })


@login_required
def send_questionnaire(request, patient_id):
    patient = get_object_or_404(User, id=patient_id, role='patient')

    if request.method == 'POST':
        questionnaire_id = request.POST.get('questionnaire_id')
        if not questionnaire_id:
            return HttpResponseBadRequest("Brak ID ankiety.")

        # Sprawdź dostępność ankiety
        questionnaire = Questionnaire.objects.filter(
            Q(owner=request.user) | Q(is_global=True),
            is_active=True,
            id=questionnaire_id
        ).first()

        if not questionnaire:
            messages.error(request, "Nie masz dostępu do tej ankiety.")
            return redirect('patient_detail', patient_id=patient.id)

        SentQuestionnaireRequest.objects.create(
            specialist=request.user,
            patient=patient,
            questionnaire=questionnaire,
            sent_at=timezone.now(),
            is_filled=False
        )
        messages.success(request, f"Ankieta „{questionnaire.name}” została wysłana.")
        return redirect(f"{reverse('patient_detail', args=[patient.id])}?tab=survey")

    return HttpResponseBadRequest("Niedozwolona metoda.")


@require_GET
@login_required
def search_questionnaires(request):
    term = request.GET.get('q', '').strip()
    if not term:
        return JsonResponse({'html': ''})

    specialist = request.user
    questionnaires = Questionnaire.objects.filter(
        Q(owner=specialist) | Q(is_global=True),
        is_active=True,
        name__icontains=term
    ).order_by('name')[:6]

    html = render_to_string('specialists/_questionnaire_list.html', {
        'questionnaires': questionnaires
    }, request=request)

    return JsonResponse({'html': html})


@login_required
def view_patient_response(request, request_id):
    filled_request = get_object_or_404(SentQuestionnaireRequest, id=request_id)

    if filled_request.specialist != request.user:
        return render(request, 'mySpecialist/view_patient_response.html', {
            'questionnaire': None,
            'sections': [],
            'answers': {},
            'access_denied': True,
        })

    questionnaire = filled_request.questionnaire
    sections = questionnaire.sections.prefetch_related('questions__choices').all()
    response = getattr(filled_request, 'response', None)

    answers = {}
    if response:
        for answer in response.answers.select_related('question').prefetch_related('selected_choices'):
            question = answer.question
            if question.question_type == 'text':
                answers[question.id] = answer.text_answer
            elif question.question_type == 'single_choice':
                selected = answer.selected_choices.first()
                answers[question.id] = selected.text if selected else ''
            elif question.question_type == 'multiple_choice':
                answers[question.id] = [choice.text for choice in answer.selected_choices.all()]

    return render(request, 'mySpecialist/view_patient_response.html', {
        'questionnaire': questionnaire,
        'sections': sections,
        'answers': answers,
    })

def lab_result_detail_specialist(request, pk):
    if not request.user.is_specialist:
        return redirect('no_permission')

    survey = get_object_or_404(LabSurveyResult, pk=pk)
    entries = list(LabResultEntry.objects.filter(survey=survey))

    test_order = {test["test_name"]: i for i, test in enumerate(get_default_lab_tests())}
    entries.sort(key=lambda e: test_order.get(e.test_name, 9999))

    grouped_entries = OrderedDict()
    for section, group in groupby(entries, key=attrgetter('section')):
        grouped_entries[section or "Inne"] = list(group)

    return render(request, 'labTest/result_detail_specialist.html', {
        'survey': survey,
        'grouped_entries': grouped_entries,
    })

def _fmt_dt(dt):
    try:
        return localtime(dt).strftime("%d.%m.%Y %H:%M")
    except Exception:
        return None

def _summarize_survey(s: SentQuestionnaireRequest) -> str:
    parts = [f"• Ankieta: {getattr(getattr(s, 'questionnaire', None), 'name', 'Ankieta')}"]
    sent  = _fmt_dt(getattr(s, "sent_at", None))
    filled = _fmt_dt(getattr(s, "filled_at", None))
    meta = []
    if sent: meta.append(f"wysłano: {sent}")
    if filled: meta.append(f"wypełniono: {filled}")
    if meta: parts.append(f"  ({', '.join(meta)})")

    # >>> KLUCZ: realne odpowiedzi
    resp = getattr(s, "response", None)
    if resp:
        try:
            answers_qs = resp.answers.select_related("question").prefetch_related("selected_choices")
        except Exception:
            answers_qs = getattr(resp, "answers", [])  # fallback

        lines = []
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
                    choice = a.selected_choices.first()
                    val = getattr(choice, "text", "") if choice else ""
                except Exception:
                    val = ""
            elif qtype == "multiple_choice":
                try:
                    val = ", ".join([getattr(c, "text", "") for c in a.selected_choices.all()])
                except Exception:
                    val = ""
            else:
                # uniwersalny fallback
                val = (
                    getattr(a, "text_answer", "")
                    or getattr(a, "value", "")
                    or ", ".join([str(x) for x in getattr(a, "selected_choices", [])])  # gdy to lista
                )

            if val not in (None, "", [], {}):
                lines.append(f"{qtext}: {val}")

        if lines:
            parts.append("  Odpowiedzi:")
            # ogranicz do sensownej długości
            snippet = "\n".join([f"    - {ln}" for ln in lines])[:1200]
            parts.append(snippet)

    return "\n".join(parts)


def _summarize_lab(l: LabSurveyResult) -> str:
    parts = [f"• Badanie: {getattr(l, 'name', str(l))}"]
    d = getattr(l, "collected_at", None) or getattr(l, "created_at", None)
    d = _fmt_dt(d)
    if d:
        parts.append(f"  data: {d}")
    short = getattr(l, "short_summary", None)
    if short:
        parts.append(f"  opis: {short}")

    # >>> KLUCZ: realne wyniki (top 10, reszta i tak by „zalała” prompt)
    try:
        entries = list(LabResultEntry.objects.filter(survey=l))[:10]
    except Exception:
        entries = []

    for e in entries:
        name = getattr(e, "test_name", None) or getattr(e, "name", None) or "Parametr"
        val  = (
            getattr(e, "value", None)
            or getattr(e, "result", None)
            or getattr(e, "result_value", None)
        )
        unit = getattr(e, "unit", None)
        ref  = (
            getattr(e, "reference_range", None)
            or getattr(e, "ref", None)
            or (
                f"{getattr(e,'ref_low', '')}–{getattr(e,'ref_high','')}"
                if hasattr(e, "ref_low") or hasattr(e, "ref_high") else None
            )
        )
        bits = [name]
        if val is not None: bits.append(str(val))
        if unit: bits.append(str(unit))
        if ref:  bits.append(f"(ref: {ref})")
        parts.append("  " + " ".join(bits))

    if len(parts) == 1:
        parts.append("  " + str(l))

    return "\n".join(parts)



@login_required
@require_POST
def run_model(request: HttpRequest):
    """
    JSON IN:
      { "model": "mistral",
        "survey_ids": [..], "lab_ids": [..],
        "prompt": "..." }

    JSON OUT:
      { "ok": true, "model": "mistral", "text": "..." }
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "Bad JSON"}, status=400)

    model = (payload.get("model") or "").lower()
    if model != "mistral":
        return JsonResponse({"ok": False, "error": "Unsupported model"}, status=400)

    survey_ids = payload.get("survey_ids") or []
    lab_ids = payload.get("lab_ids") or []
    user_prompt = (payload.get("prompt") or "").strip()

    # pobranie danych
    surveys = list(SentQuestionnaireRequest.objects.filter(id__in=survey_ids)) if survey_ids else []
    labs = list(LabSurveyResult.objects.filter(id__in=lab_ids)) if lab_ids else []

    # zbuduj kontekst
    ctx_lines = []
    if surveys:
        ctx_lines.append("### Ankiety (wybrane):")
        for s in surveys:
            ctx_lines.append(_summarize_survey(s))
    if labs:
        ctx_lines.append("")
        ctx_lines.append("### Badania laboratoryjne (wybrane):")
        for l in labs:
            ctx_lines.append(_summarize_lab(l))

    context_block = "\n".join(ctx_lines).strip()
    # główny prompt
    system_header = (
        "Jesteś asystentem medycznym. Odpowiadasz krótko po polsku, bez halucynacji. "
        "Nie tłumacz treści z kontekstu ani nie przepisuj ankiet. "
        "Jeśli danych brakuje – napisz to wprost i zasugeruj ścieżkę przez POZ."
    )

    fewshot = """
    PRZYKŁAD 1
    Kontekst:
    - Objawy: ból w klatce piersiowej przy wysiłku, nadciśnienie
    - Leki: amlodypina
    - Badanie: EKG bez zmian ostrych
    Pytanie: Do jakiego specjalisty powinien trafić pacjent?
    Odpowiedź:
    - Specjalista: kardiolog
    - Pilność: pilne (objawy wieńcowe)
    - Dlaczego: ból dławicowy + czynniki ryzyka; potrzebna diagnostyka (test wysiłkowy/echo)
    - Co przygotować: lista leków, tygodniowe pomiary ciśnienia

    PRZYKŁAD 2
    Kontekst:
    - Objawy: drętwienie prawej ręki okresowo, bóle karku
    - Badanie: morfologia w normie
    Pytanie: Do jakiego specjalisty powinien trafić pacjent?
    Odpowiedź:
    - Specjalista: neurolog (ew. ortopeda kręgosłupa)
    - Pilność: planowa
    - Dlaczego: parestezje kończyny górnej; różnicowanie neuro/ortopedyczne
    - Co przygotować: opis napadów (czas, wyzwalacze), ewentualne badania obrazowe
    """.strip()

    task = (
        "ZADANIE: Na podstawie KONTEKSTU wskaż najlepiej pasującego specjalistę (1–2 specjalistów), "
        "podaj krótko pilność (pilne/planowe/na już) i 1–3 powody. Dodaj mini-checklistę 'Co przygotować'. "
        "Jeśli nie da się wskazać, napisz: 'Na podstawie dostępnych danych nie można jednoznacznie wskazać specjalisty.' "
        "i zasugeruj kontakt z lekarzem POZ z powodem. Maksymalnie 6 linijek."
    )

    parts = [system_header]
    if context_block:
        parts += ["\nKontekst pacjenta:", context_block]

    if user_prompt:
        parts += [
            "\nPolecenie użytkownika:", user_prompt,
            "\nWskazówki:",
            "Użyj maksymalnie 8 linijek. Punkty wypisz myślnikami. Odwołuj się tylko do faktów z kontekstu.",
            "\nTwoja odpowiedź:"
        ]
    else:
        parts += [
            "\nPrzykłady:", fewshot,
            "\nPytanie:", "Do jakiego specjalisty powinien trafić pacjent?",
            task,
            "\nTwoja odpowiedź:"
        ]

    final_prompt = "\n\n".join(parts).strip()

    try:
        text = generate_text(final_prompt, max_new_tokens=500)
        return JsonResponse({"ok": True, "model": "mistral", "text": text})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

def _survey_to_text(s: SentQuestionnaireRequest) -> str:
    parts = [f"Ankieta: {getattr(s.questionnaire, 'name', '—')}"]
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
    elif hasattr(s, "answers") and s.answers:
        parts.append(f"Surowe_odp: {str(s.answers)[:400]}…")

    return "\n".join(parts)


def _lab_to_text(l: LabSurveyResult) -> str:
    parts = [f"Badanie: {getattr(l, 'name', str(l))}"]
    if getattr(l, "collected_at", None):
        parts.append(f"Data: {_fmt_dt(l.collected_at)}")
    if getattr(l, "short_summary", None):
        parts.append(f"Podsumowanie: {l.short_summary}")

    try:
        entries = list(LabResultEntry.objects.filter(survey=l))[:15]
    except Exception:
        entries = []

    for e in entries:
        name = getattr(e, "test_name", None) or getattr(e, "name", None) or "Parametr"
        val  = getattr(e, "value", None) or getattr(e, "result", None) or getattr(e, "result_value", None)
        unit = getattr(e, "unit", None)
        ref  = getattr(e, "reference_range", None) or getattr(e, "ref", None)
        bits = [name]
        if val is not None: bits.append(str(val))
        if unit: bits.append(str(unit))
        if ref:  bits.append(f"(ref: {ref})")
        parts.append(" - " + " ".join(bits))

    return "\n".join(parts)


def _build_prompt(base_prompt: str, surveys, labs) -> str:
    # zbuduj kontekst na bazie istniejących helperów
    ctx_lines = []
    if surveys:
        ctx_lines.append("### Ankiety (wybrane):")
        for s in surveys:
            ctx_lines.append(_survey_to_text(s))
    if labs:
        if ctx_lines:
            ctx_lines.append("")
        ctx_lines.append("### Badania laboratoryjne (wybrane):")
        for l in labs:
            ctx_lines.append(_lab_to_text(l))
    context_block = "\n".join(ctx_lines).strip() or "(brak danych)"

    system_header = (
        "Jesteś asystentem medycznym. Odpowiadasz krótko po polsku, bez halucynacji. "
        "Nie tłumacz treści z kontekstu ani nie przepisuj ankiet. "
        "Jeśli danych brakuje – napisz to wprost i zasugeruj ścieżkę przez POZ."
    )

    fewshot = """
PRZYKŁAD 1
Kontekst:
- Objawy: ból w klatce piersiowej przy wysiłku, nadciśnienie
- Leki: amlodypina
- Badanie: EKG bez zmian ostrych
Pytanie: Do jakiego specjalisty powinien trafić pacjent?
Odpowiedź:
- Specjalista: kardiolog
- Pilność: pilne (objawy wieńcowe)
- Dlaczego: ból dławicowy + czynniki ryzyka; potrzebna diagnostyka (test wysiłkowy/echo)
- Co przygotować: lista leków, tygodniowe pomiary ciśnienia

PRZYKŁAD 2
Kontekst:
- Objawy: drętwienie prawej ręki okresowo, bóle karku
- Badanie: morfologia w normie
Pytanie: Do jakiego specjalisty powinien trafić pacjent?
Odpowiedź:
- Specjalista: neurolog (ew. ortopeda kręgosłupa)
- Pilność: planowa
- Dlaczego: parestezje kończyny górnej; różnicowanie neuro/ortopedyczne
- Co przygotować: opis napadów (czas, wyzwalacze), ewentualne badania obrazowe
""".strip()

    task = (
        "ZADANIE: Na podstawie KONTEKSTU wskaż najlepiej pasującego specjalistę (1–2 specjalistów), "
        "podaj krótko pilność (pilne/planowe/na już) i 1–3 powody. Dodaj mini-checklistę 'Co przygotować'. "
        "Jeśli nie da się wskazać, napisz: 'Na podstawie dostępnych danych nie można jednoznacznie wskazać specjalisty.' "
        "i zasugeruj kontakt z lekarzem POZ z powodem. Maksymalnie 6 linijek."
    )

    parts = [system_header, "Kontekst pacjenta:", context_block]

    if (base_prompt or "").strip():
        parts += [
            "Polecenie użytkownika:", base_prompt.strip(),
            "Wskazówki:", "Użyj maksymalnie 8 linijek. Punkty wypisz myślnikami. Odwołuj się tylko do faktów z kontekstu.",
            "Twoja odpowiedź:"
        ]
    else:
        parts += [
            "Przykłady:", fewshot,
            "Pytanie:", "Do jakiego specjalisty powinien trafić pacjent?",
            task,
            "Twoja odpowiedź:"
        ]

    return "\n\n".join(parts).strip()

def _get_selected_surveys(ids):
    if not ids:
        return []
    return list(SentQuestionnaireRequest.objects.filter(id__in=ids))

def _get_selected_labs(ids):
    if not ids:
        return []
    return list(LabSurveyResult.objects.filter(id__in=ids))

from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
@csrf_exempt  # usuń jeśli dodasz CSRF token w fetch (polecam użyć tokenu! — patrz JS niżej)
@require_POST
# @login_required
def run_analysis_api(request):
    """
    JSON IN: {
      "model": "mistral" | "mistral_rag" | "herbert" | "xgboost",
      "prompt": "...",
      "survey_ids": [..],
      "lab_ids": [..]
    }

    JSON OUT:
      - Mistral / Mistral RAG:
          { ok, model, text, sources?[], raw?{} }
      - HerBERT / XGBoost:
          {
            ok, model,
            predicted_label,                     # str
            probs: [{label, percent, prob}],     # percent 0..100, prob 0..1
            raw_features,                        # debug: co zassało z ankiet/labów
            raw_payload                          # debug: tekst wejściowy (HerBERT/XGB)
          }
    """
    # --- parse ---
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)

    model = (payload.get("model") or "").lower()
    prompt = payload.get("prompt") or ""
    survey_ids = payload.get("survey_ids") or []
    lab_ids = payload.get("lab_ids") or []

    # --- fetch data ---
    surveys = (
        list(
            SentQuestionnaireRequest.objects
            .filter(id__in=survey_ids)
            .select_related("questionnaire")
            .prefetch_related("response__answers__question", "response__answers__selected_choices")
        )
        if survey_ids else []
    )
    labs = list(LabSurveyResult.objects.filter(id__in=lab_ids)) if lab_ids else []

    # --- wspólny prompt dla Mistrala (LLM) ---
    full_prompt = _build_prompt(prompt, surveys, labs)

    try:
        # ---------------- MISTRAL (bez RAG) ----------------
        if model == "mistral":
            text = generate_text(full_prompt, max_new_tokens=400)
            return JsonResponse({"ok": True, "model": "mistral", "text": text, "raw": {"tokens": len(full_prompt)}})

        # ---------------- MISTRAL (RAG) ----------------
        elif model == "mistral_rag":
            # krótka „podpowiedź” do retrievalu: prompt + skrót ankiet/badań
            surveys_text = "\n\n".join(_survey_to_text(s) for s in surveys) if surveys else ""
            labs_text = "\n\n".join(_lab_to_text(l) for l in labs) if labs else ""
            retrieval_hint = (surveys_text + ("\n\n" if surveys_text and labs_text else "") + labs_text).strip()[:1200]
            question_for_rag = (prompt.strip() or "Dobierz specjalistę i zalecenia dla pacjenta.") + (
                f"\n\nKontekst pacjenta (skrót):\n{retrieval_hint}" if retrieval_hint else ""
            )

            try:
                text, hits, _aug = generate_with_rag(
                    final_prompt=full_prompt,
                    question_for_retrieval=question_for_rag,
                    k=3,
                    gen_kwargs={"max_new_tokens": 400}
                )
            except FileNotFoundError as e:
                return JsonResponse({"ok": False, "error": f"Brak artefaktów RAG: {e}"}, status=500)
            except Exception as e:
                return JsonResponse({"ok": False, "error": f"Błąd RAG: {e}"}, status=500)

            # zbuduj źródła do UI
            sources = []
            for h in hits:
                preview = (h.get("text") or "").replace("\n", " ")
                if len(preview) > 200:
                    preview = preview[:200] + "…"
                sources.append({
                    "rank": h.get("rank"),
                    "score": h.get("score"),
                    "doc_name": h.get("doc_name"),
                    "chunk_idx": h.get("chunk_idx"),
                    "preview": preview
                })

            return JsonResponse({
                "ok": True,
                "model": "mistral_rag",
                "text": text,
                "sources": sources,
                "raw": {"tokens": len(full_prompt)}
            })

        # ---------------- HerBERT (klasyfikacja) ----------------
        elif model == "herbert":
            if not surveys:
                return JsonResponse(
                    {"ok": False, "error": "Dla HerBERT wybierz przynajmniej jedną wypełnioną ankietę."},
                    status=400
                )

            res = herbert_predict(surveys)  # {'predicted_label','classes','raw_features','raw_payload'}

            probs_ui = []
            for c in res.get("classes", []):
                prob = float(c.get("prob", 0.0))
                percent = float(c.get("percent", prob * 100.0))
                probs_ui.append({
                    "label": c.get("label", ""),
                    "percent": round(percent, 2),
                    "prob": round(prob, 6)
                })

            return JsonResponse({
                "ok": True,
                "model": "herbert",
                "predicted_label": res.get("predicted_label", "—"),
                "probs": probs_ui,
                "raw_features": res.get("raw_features"),
                "raw_payload": res.get("raw_payload"),
            })

        # ---------------- XGBOOST (embedding HerBERT + wybrane laby) ----------------
        elif model == "xgboost":
            if not surveys and not labs:
                return JsonResponse(
                    {"ok": False, "error": "XGBoost wymaga przynajmniej ankiet lub badań."},
                    status=400
                )

            res = xgb_predict(surveys, labs)  # {'predicted_label','classes','raw_features','raw_payload'}

            probs_ui = []
            for c in res.get("classes", []):
                prob = float(c.get("prob", 0.0))
                percent = float(c.get("percent", prob * 100.0))
                probs_ui.append({
                    "label": c.get("label", ""),
                    "percent": round(percent, 2),
                    "prob": round(prob, 6)
                })

            return JsonResponse({
                "ok": True,
                "model": "xgboost",
                "predicted_label": res.get("predicted_label", "—"),
                "probs": probs_ui,
                "raw_features": res.get("raw_features"),
                "raw_payload": res.get("raw_payload"),
            })

        # ---------------- nieobsługiwany model ----------------
        else:
            return JsonResponse(
                {"ok": False, "error": f"Model '{model}' nie jest obsługiwany w tym endpointzie."}, status=400
            )

    except Exception as ex:
        # bardziej czytelny komunikat (zamiast np. „0” z KeyError(0))
        msg = ", ".join([str(a) for a in getattr(ex, "args", [])]) or str(ex)
        if model == "herbert":
            prefix = "HERBERT: "
        elif model == "xgboost":
            prefix = "XGBOOST: "
        elif model == "mistral_rag":
            prefix = "RAG: "
        else:
            prefix = "Błąd modelu: "
        return JsonResponse({"ok": False, "error": f"{prefix}{msg}"}, status=500)
