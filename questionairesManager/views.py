from django.shortcuts import render, get_object_or_404, redirect
from django.forms import modelformset_factory
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q

from .models import Questionnaire, Question, Choice, Section
from .forms import QuestionForm, SectionForm


def questionnaire_list(request):
    query = request.GET.get('q', '')
    questionnaires = Questionnaire.objects.filter(
        Q(owner=request.user) | Q(is_global=True),
        name__icontains=query
    ).order_by('name')

    paginator = Paginator(questionnaires, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string("questionairesManager/_questionnaire_cards.html", {
            'questionnaires': page_obj.object_list,
        })
        return HttpResponse(html)

    return render(request, 'questionairesManager/questionnaire_list.html', {
        'page_obj': page_obj,
        'query': query
    })


@csrf_exempt
def rename_questionnaire(request, pk):
    if request.method == 'POST':
        questionnaire = get_object_or_404(Questionnaire, pk=pk)

        if questionnaire.is_global:
            return JsonResponse({'error': 'Nie można zmieniać nazwy domyślnej ankiety.'}, status=403)

        new_name = request.POST.get('name')

        conflict = Questionnaire.objects.filter(
            Q(owner=request.user) | Q(is_global=True),
            name=new_name
        ).exclude(pk=questionnaire.pk).exists()

        if conflict:
            return JsonResponse({'error': 'duplicate'}, status=400)

        questionnaire.name = new_name
        questionnaire.save()
        return JsonResponse({'new_name': new_name})


def create_questionnaire(request):
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()

        if not name:
            return JsonResponse({"success": False, "message": "Nazwa nie może być pusta."})

        conflict = Questionnaire.objects.filter(
            Q(owner=request.user) | Q(is_global=True),
            name__iexact=name
        ).exists()

        if conflict:
            return JsonResponse({"success": False, "message": "Ankieta o takiej nazwie już istnieje."})

        Questionnaire.objects.create(name=name, owner=request.user)
        return JsonResponse({"success": True})

    return redirect('questionairesManager:questionnaire_list')


def copy_questionnaire(request, pk):
    original = get_object_or_404(Questionnaire, pk=pk)
    base_name = f"{original.name} (Copy)"
    name = base_name
    counter = 2

    while Questionnaire.objects.filter(Q(owner=request.user) | Q(is_global=True), name=name).exists():
        name = f"{base_name} {counter}"
        counter += 1

    copy = Questionnaire.objects.create(name=name, owner=request.user)

    for section in original.sections.all():
        new_section = Section.objects.create(name=section.name, questionnaire=copy)
        for question in section.questions.all():
            new_question = Question.objects.create(
                questionnaire=copy,
                section=new_section,
                question_text=question.question_text,
                question_type=question.question_type,
                order=question.order
            )
            for choice in question.choices.all():
                Choice.objects.create(question=new_question, text=choice.text)

    messages.success(request, "Ankieta została skopiowana.")
    return redirect('questionairesManager:questionnaire_list')


def questionnaire_detail(request, pk):
    questionnaire = get_object_or_404(Questionnaire, pk=pk)
    sections = questionnaire.sections.prefetch_related('questions__choices').all()
    questions_without_section = questionnaire.questions.filter(section__isnull=True).prefetch_related('choices')

    return render(request, 'questionairesManager/questionnaire_detail.html', {
        'questionnaire': questionnaire,
        'sections': sections,
        'questions_without_section': questions_without_section,
    })


def edit_questionnaire(request, pk):
    questionnaire = get_object_or_404(Questionnaire, pk=pk)

    if questionnaire.is_global:
        messages.error(request, "Nie możesz edytować domyślnej ankiety. Skopiuj ją, aby wprowadzić zmiany.")
        return redirect('questionairesManager:questionnaire_detail', pk=pk)

    QuestionFormSet = modelformset_factory(
        Question,
        form=QuestionForm,
        extra=0,
        can_delete=True
    )

    questions = questionnaire.questions.select_related('section').all()
    sections = questionnaire.sections.all()
    section_form = SectionForm()

    if request.method == 'POST':
        post_data = request.POST.copy()

        new_name = post_data.get('questionnaire-name', '').strip()
        if new_name and new_name != questionnaire.name:
            questionnaire.name = new_name
            questionnaire.save()

        section_titles = post_data.getlist('section_titles[]')
        existing_names = set(sections.values_list('name', flat=True))
        for title in section_titles:
            title = title.strip()
            if title and title not in existing_names:
                Section.objects.create(name=title, questionnaire=questionnaire)

                existing_names.add(title)

        deleted_section_ids = post_data.getlist('deleted_sections[]')
        for section_id in deleted_section_ids:
            if section_id.isdigit():
                try:
                    Section.objects.get(id=section_id, questionnaire=questionnaire).delete()
                except Section.DoesNotExist:
                    pass

        all_sections = questionnaire.sections.all()
        section_name_to_id = {s.name.strip(): s.id for s in all_sections}

        total_forms = int(post_data.get('form-TOTAL_FORMS', 0))

        for i in range(total_forms):
            section_field = f'form-{i}-section'
            val = post_data.get(section_field)
            if val and not val.isdigit():
                post_data[section_field] = str(section_name_to_id.get(val.strip(), ''))

        formset = QuestionFormSet(post_data, queryset=questions)

        if formset.is_valid():
            instances = formset.save(commit=False)
            for form in formset:
                if form in formset.deleted_forms:
                    if form.instance.pk:
                        form.instance.delete()
                    continue

                question = form.save(commit=False)
                question.questionnaire = questionnaire
                question.save()

                if question.question_type in ['single_choice', 'multiple_choice']:
                    question.choices.all().delete()
                    choices_raw = form.cleaned_data.get('choices_text', '')
                    for text in [c.strip() for c in choices_raw.split(',') if c.strip()]:
                        Choice.objects.create(question=question, text=text)

            formset.save_m2m()
            return redirect('questionairesManager:questionnaire_detail', pk=pk)

    else:
        formset = QuestionFormSet(queryset=questions)

    return render(request, 'questionairesManager/edit_questionnaire_bulk.html', {
        'questionnaire': questionnaire,
        'formset': formset,
        'section_form': section_form,
        'sections': sections,
    })


@require_POST
def delete_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    questionnaire_id = question.questionnaire.id
    question.delete()
    return redirect('questionairesManager:edit_questionnaire', pk=questionnaire_id)


def delete_questionnaire(request, pk):
    questionnaire = get_object_or_404(Questionnaire, pk=pk)

    if questionnaire.is_global:
        messages.error(request, "Nie możesz usunąć domyślnej ankiety.")
        return redirect('questionairesManager:questionnaire_detail', pk=pk)

    if request.method == 'POST':
        questionnaire.delete()
        messages.success(request, "Ankieta została usunięta.")
        return redirect('questionairesManager:questionnaire_list')

    messages.error(request, "Nieprawidłowe żądanie.")
    return redirect('questionairesManager:questionnaire_detail', pk=pk)


# ✅ POPRAWIONA FUNKCJA — teraz uwzględnia również ankiety globalne!
def search_questionnaires_ajax(request):
    query = request.GET.get("q", "")
    questionnaires = Questionnaire.objects.filter(
        Q(owner=request.user) | Q(is_global=True)
    )

    if query:
        questionnaires = questionnaires.filter(name__icontains=query)

    html = render_to_string("questionairesManager/_questionnaire_cards.html", {
        "questionnaires": questionnaires
    })

    return JsonResponse({"html": html})


@require_POST
def create_section_ajax(request, questionnaire_id):
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    section_name = request.POST.get("section_name", "").strip()

    if not section_name:
        return JsonResponse({"error": "Brak nazwy sekcji."}, status=400)

    if Section.objects.filter(questionnaire=questionnaire, name__iexact=section_name).exists():
        return JsonResponse({"error": "Sekcja o tej nazwie już istnieje."}, status=400)

    section = Section.objects.create(name=section_name, questionnaire=questionnaire)

    return JsonResponse({
        "id": section.id,
        "name": section.name
    })
