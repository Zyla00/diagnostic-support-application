from collections import defaultdict
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import formset_factory
from .forms import LabSurveyResultForm, LabResultEntryForm
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from .models import LabSurveyResult
LabResultEntryFormSet = formset_factory(LabResultEntryForm, extra=0)
FORMSET_PREFIX = 'labresult'




def get_default_lab_tests():
    return [
      { "section": "Hematologia", "test_name": "Morfologia krwi obwodowej z płytkami", "value_type": "numeric", "unit": "" },
      { "section": "Hematologia", "test_name": "Morfologia z rozmazem", "value_type": "text", "unit": "" },
      { "section": "Hematologia", "test_name": "Retikulocyty", "value_type": "numeric", "unit": "%" },
      { "section": "Hematologia", "test_name": "Odczyn Biernackiego (OB)", "value_type": "numeric", "unit": "mm/h" },

      { "section": "Hematologia", "test_name": "WBC", "value_type": "numeric", "unit": "10^3/μL" },
      { "section": "Hematologia", "test_name": "RBC", "value_type": "numeric", "unit": "10^6/μL" },
      { "section": "Hematologia", "test_name": "Hemoglobina (HGB)", "value_type": "numeric", "unit": "g/dL" },
      { "section": "Hematologia", "test_name": "Hematokryt (HCT)", "value_type": "numeric", "unit": "%" },
      { "section": "Hematologia", "test_name": "MCV", "value_type": "numeric", "unit": "fL" },
      { "section": "Hematologia", "test_name": "MCH", "value_type": "numeric", "unit": "pg" },
      { "section": "Hematologia", "test_name": "MCHC", "value_type": "numeric", "unit": "g/dL" },
      { "section": "Hematologia", "test_name": "RDW", "value_type": "numeric", "unit": "%" },
      { "section": "Hematologia", "test_name": "Płytki krwi (PLT)", "value_type": "numeric", "unit": "10^3/μL" },
      { "section": "Hematologia", "test_name": "Neutrofile (abs.)", "value_type": "numeric", "unit": "10^3/μL" },
      { "section": "Hematologia", "test_name": "Limfocyty (abs.)", "value_type": "numeric", "unit": "10^3/μL" },
      { "section": "Hematologia", "test_name": "Monocyty (abs.)", "value_type": "numeric", "unit": "10^3/μL" },
      { "section": "Hematologia", "test_name": "Eozynofile (abs.)", "value_type": "numeric", "unit": "10^3/μL" },
      { "section": "Hematologia", "test_name": "Bazofile (abs.)", "value_type": "numeric", "unit": "10^3/μL" },

      { "section": "Biochemia", "test_name": "Sód (Na⁺)", "value_type": "numeric", "unit": "mmol/L" },
      { "section": "Biochemia", "test_name": "Potas (K⁺)", "value_type": "numeric", "unit": "mmol/L" },
      { "section": "Biochemia", "test_name": "Chlorki (Cl⁻)", "value_type": "numeric", "unit": "mmol/L" },
      { "section": "Biochemia", "test_name": "Wapń zjonizowany", "value_type": "numeric", "unit": "mmol/L" },
      { "section": "Biochemia", "test_name": "Żelazo", "value_type": "numeric", "unit": "μg/dL" },
      { "section": "Biochemia", "test_name": "TIBC", "value_type": "numeric", "unit": "μg/dL" },
      { "section": "Biochemia", "test_name": "Transferryna", "value_type": "numeric", "unit": "mg/dL" },
      { "section": "Biochemia", "test_name": "Ferrytyna", "value_type": "numeric", "unit": "ng/mL" },
      { "section": "Biochemia", "test_name": "Glukoza", "value_type": "numeric", "unit": "mg/dL" },
      { "section": "Biochemia", "test_name": "Test obciążenia glukozą", "value_type": "numeric", "unit": "mg/dL" },
      { "section": "Biochemia", "test_name": "Hemoglobina glikowana (HbA1c)", "value_type": "numeric", "unit": "%" },
      { "section": "Biochemia", "test_name": "Mocznik", "value_type": "numeric", "unit": "mg/dL" },
      { "section": "Biochemia", "test_name": "Kreatynina", "value_type": "numeric", "unit": "mg/dL" },
      { "section": "Biochemia", "test_name": "eGFR", "value_type": "numeric", "unit": "mL/min/1.73 m²" },
      { "section": "Biochemia", "test_name": "Kwas moczowy", "value_type": "numeric", "unit": "mg/dL" },
      { "section": "Biochemia", "test_name": "Białko całkowite", "value_type": "numeric", "unit": "g/dL" },
      { "section": "Biochemia", "test_name": "Albumina", "value_type": "numeric", "unit": "g/dL" },
      { "section": "Biochemia", "test_name": "CRP", "value_type": "numeric", "unit": "mg/L" },
      { "section": "Biochemia", "test_name": "ALT", "value_type": "numeric", "unit": "U/L" },
      { "section": "Biochemia", "test_name": "AST", "value_type": "numeric", "unit": "U/L" },
      { "section": "Biochemia", "test_name": "ALP", "value_type": "numeric", "unit": "U/L" },
      { "section": "Biochemia", "test_name": "GGTP", "value_type": "numeric", "unit": "U/L" },
      { "section": "Biochemia", "test_name": "CK", "value_type": "numeric", "unit": "U/L" },
      { "section": "Biochemia", "test_name": "Cholesterol całkowity", "value_type": "numeric", "unit": "mg/dL" },
      { "section": "Biochemia", "test_name": "HDL", "value_type": "numeric", "unit": "mg/dL" },
      { "section": "Biochemia", "test_name": "LDL", "value_type": "numeric", "unit": "mg/dL" },
      { "section": "Biochemia", "test_name": "Triglicerydy", "value_type": "numeric", "unit": "mg/dL" },
      { "section": "Biochemia", "test_name": "ApoB", "value_type": "numeric", "unit": "mg/dL" },
      { "section": "Biochemia", "test_name": "Bilirubina całkowita", "value_type": "numeric", "unit": "mg/dL" },

      { "section": "Hormony", "test_name": "TSH", "value_type": "numeric", "unit": "μIU/mL" },
      { "section": "Hormony", "test_name": "FT3", "value_type": "numeric", "unit": "pg/mL" },
      { "section": "Hormony", "test_name": "FT4", "value_type": "numeric", "unit": "ng/dL" },

      { "section": "Układ krzepnięcia", "test_name": "INR", "value_type": "numeric", "unit": "" },
      { "section": "Układ krzepnięcia", "test_name": "APTT", "value_type": "numeric", "unit": "s" },
      { "section": "Układ krzepnięcia", "test_name": "Fibrynogen", "value_type": "numeric", "unit": "g/L" },

      { "section": "Mikrobiologia", "test_name": "Posiew moczu z antybiogramem", "value_type": "text", "unit": "" },
      { "section": "Mikrobiologia", "test_name": "Strep-test", "value_type": "choice", "unit": "" },
      { "section": "Mikrobiologia", "test_name": "Antygen SARS-CoV-2", "value_type": "choice", "unit": "" },

      { "section": "Mocz", "test_name": "Ogólne badanie moczu", "value_type": "text", "unit": "" },

      { "section": "Kał", "test_name": "Krew utajona", "value_type": "choice", "unit": "" },
      { "section": "Kał", "test_name": "Antygen H. pylori", "value_type": "choice", "unit": "" },

      { "section": "Parametry życiowe", "test_name": "Temperatura ciała", "value_type": "numeric", "unit": "°C" }
    ]


# initial_data = get_default_lab_tests()
# LabResultEntryFormSet = formset_factory(LabResultEntryForm, extra=len(initial_data))


def group_forms_by_section(formset):
    grouped = defaultdict(list)
    for form in formset:
        section = form.initial.get('section', 'Inne')
        grouped[section].append(form)
    return grouped

def new_survey(request):
    if request.method == 'POST':
        survey_form = LabSurveyResultForm(request.POST)
        formset = LabResultEntryFormSet(request.POST, prefix='labresult')

        if survey_form.is_valid() and formset.is_valid():
            survey = survey_form.save(commit=False)
            survey.patient = request.user
            survey.save()

            for form in formset:
                cd = form.cleaned_data
                if cd.get('test_name'):  # zabezpieczenie przed pustymi formularzami
                    LabResultEntry.objects.create(
                        survey=survey,
                        section=cd.get('section'),
                        test_name=cd.get('test_name'),
                        value=cd.get('value'),
                        value_type=cd.get('value_type'),
                        unit=cd.get('unit'),
                        reference_min=cd.get('reference_min'),
                        reference_max=cd.get('reference_max')
                    )

            return redirect('labTest:dashboard')

    else:  # GET
        initial_data = get_default_lab_tests()
        survey_form = LabSurveyResultForm()
        formset = LabResultEntryFormSet(initial=initial_data, prefix='labresult')

        grouped_formset = {}
        for form in formset:
            section = form.initial.get('section', 'Inne')
            grouped_formset.setdefault(section, []).append(form)

        return render(request, 'labTest/new_survey.html', {
            'survey_form': survey_form,
            'formset': formset,
            'grouped_formset': grouped_formset,
        })

    return render(request, 'labTest/new_survey.html', {
        'survey_form': survey_form,
        'formset': formset,
        'grouped_formset': {},
    })


def dashboard(request):
    surveys = LabSurveyResult.objects.filter(patient=request.user).order_by('-created_at')

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        surveys = surveys.filter(created_at__date__gte=parse_date(start_date))
    if end_date:
        surveys = surveys.filter(created_at__date__lte=parse_date(end_date))

    paginator = Paginator(surveys, 12)
    page = request.GET.get('page')
    surveys_page = paginator.get_page(page)

    return render(request, 'labTest/dashboard.html', {
        'surveys': surveys_page,
        'request': request,
    })



from django.shortcuts import render, get_object_or_404
from .models import LabSurveyResult, LabResultEntry

from collections import OrderedDict
from itertools import groupby
from operator import attrgetter

def result_detail(request, pk):
    survey = get_object_or_404(LabSurveyResult, pk=pk, patient=request.user)
    entries = list(LabResultEntry.objects.filter(survey=survey))

    test_order = {test["test_name"]: i for i, test in enumerate(get_default_lab_tests())}

    entries.sort(key=lambda e: test_order.get(e.test_name, 9999))  # 9999 na końcu jeśli nieznany

    grouped_entries = OrderedDict()
    for section, group in groupby(entries, key=attrgetter('section')):
        grouped_entries[section or "Inne"] = list(group)

    return render(request, 'labTest/result_detail.html', {
        'survey': survey,
        'grouped_entries': grouped_entries
    })



