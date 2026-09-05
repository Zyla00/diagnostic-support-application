from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SentQuestionnaireRequest, QuestionnaireResponse, Answer
from questionairesManager.models import Question
from collections import defaultdict
from authCustom.models import CustomUser
from questionairesManager.models import Questionnaire, Question, Choice
from .forms import SendQuestionnaireForm
from .models import SentQuestionnaireRequest, QuestionnaireResponse, Answer


@login_required
def send_questionnaire_and_history(request, patient_id):
    if request.user.role != 'specialist':
        return redirect('dashboard')

    patient = get_object_or_404(CustomUser, id=patient_id, role='patient')

    query = request.GET.get("q", "")
    questionnaires = Questionnaire.objects.filter(
        Q(is_global=True) | Q(owner=request.user)
    )

    if query:
        questionnaires = questionnaires.filter(name__icontains=query)

    if request.method == 'POST':
        form = SendQuestionnaireForm(request.POST, specialist=request.user)
        if form.is_valid():
            questionnaire = form.cleaned_data['questionnaire']
            SentQuestionnaireRequest.objects.create(
                specialist=request.user,
                patient=patient,
                questionnaire=questionnaire,
                sent_at=timezone.now(),
                is_filled=False
            )
            messages.success(request, f"Wysłano ankietę: {questionnaire.name}")
            return redirect('send_questionnaire_and_history', patient_id=patient.id)
    else:
        form = SendQuestionnaireForm(specialist=request.user)

    history = SentQuestionnaireRequest.objects.filter(
        patient=patient
    ).select_related('questionnaire').order_by('-sent_at')

    return render(request, 'questionnairesPatient/send_questionnaire.html', {
        'patient': patient,
        'questionnaires': questionnaires,
        'query': query,
        'form': form,
        'history': history,
    })


@login_required
def patient_questionnaires(request):
    if request.user.role != 'patient':
        return redirect('specialist-dashboard')

    search_query = request.GET.get("q", "")

    all_requests = SentQuestionnaireRequest.objects.filter(
        patient=request.user
    ).select_related('questionnaire').order_by('-sent_at')

    if search_query:
        all_requests = all_requests.filter(questionnaire__name__icontains=search_query)

    pending_questionnaires = all_requests.filter(is_filled=False)
    filled_questionnaires = all_requests.filter(is_filled=True)

    return render(request, 'questionnairesPatient/patient_questionnaires.html', {
        'pending_questionnaires': pending_questionnaires,
        'filled_questionnaires': filled_questionnaires,
        'query': search_query,
    })

@login_required
def fill_questionnaire(request, request_id):
    filled_request = get_object_or_404(SentQuestionnaireRequest, id=request_id, patient=request.user)
    questionnaire = filled_request.questionnaire
    sections = questionnaire.sections.all()

    if filled_request.is_filled:
        # Tryb podglądu
        response = getattr(filled_request, 'response', None)
        answers = {}

        if response:
            for answer in response.answers.all():
                if answer.question.question_type == 'text':
                    answers[answer.question.id] = answer.text_answer
                elif answer.question.question_type == 'single_choice':
                    selected = answer.selected_choices.first()
                    answers[answer.question.id] = selected.text if selected else ''
                elif answer.question.question_type == 'multiple_choice':
                    answers[answer.question.id] = [c.text for c in answer.selected_choices.all()]

        return render(request, 'questionnairesPatient/fill_questionnaire_form.html', {
            'questionnaire': questionnaire,
            'sections': sections,
            'readonly': True,
            'answers': answers,
            'request_id': request_id,
        })

    if request.method == 'POST':
        # Tworzenie odpowiedzi
        response = QuestionnaireResponse.objects.create(request=filled_request)

        for question in questionnaire.questions.all():
            key_prefix = f"question_{question.id}"
            answer = Answer.objects.create(response=response, question=question)

            if question.question_type == 'text':
                answer.text_answer = request.POST.get(key_prefix, '').strip()
                answer.save()

            elif question.question_type == 'single_choice':
                selected = request.POST.get(key_prefix)
                if selected:
                    choice_obj = question.choices.filter(text=selected).first()
                    if choice_obj:
                        answer.selected_choices.add(choice_obj)

            elif question.question_type == 'multiple_choice':
                selected_values = request.POST.getlist(f"{key_prefix}[]")
                for val in selected_values:
                    choice_obj = question.choices.filter(text=val).first()
                    if choice_obj:
                        answer.selected_choices.add(choice_obj)

        filled_request.is_filled = True
        filled_request.save()

        messages.success(request, "Ankieta została pomyślnie wypełniona i zapisana.")
        return redirect('patient_questionnaires')

    # GET – formularz wypełniania
    return render(request, 'questionnairesPatient/fill_questionnaire_form.html', {
        'questionnaire': questionnaire,
        'sections': sections,
        'readonly': False,  # <- TO JEST WAŻNE
        'request_id': request_id,
    })