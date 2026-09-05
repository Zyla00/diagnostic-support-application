from django.urls import path
from . import views
from .views import view_patient_response
from .views import run_analysis_api



urlpatterns = [
    path('', views.specialist_list, name='specialist_list'),
    path('choose/<int:specialist_id>/', views.choose_specialist, name='choose_specialist'),
    path('resign/', views.resign_specialist, name='resign_specialist'),
    path('my-patients/', views.my_patients, name='my_patients'),
    path('my-patients/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('send-questionnaire/<int:patient_id>/', views.send_questionnaire, name='send_questionnaire'),
    path('search-questionnaires/', views.search_questionnaires, name='search_questionnaires'),
    path('questionnaire-preview/<int:questionnaire_id>/', views.questionnaire_preview_or_answers, name='questionnaire_preview'),
    path('response/<int:request_id>/', view_patient_response, name='view_patient_response'),
    path('moje-rekomendacje/', views.my_recommendations, name='my_recommendations'),
    path('specialist/lab-result/<int:pk>/', views.lab_result_detail_specialist, name='lab_result_detail_specialist'),

    path("api/run/", run_analysis_api, name="api-run"),


]
