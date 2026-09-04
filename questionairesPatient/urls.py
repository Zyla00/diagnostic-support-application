from django.urls import path
from . import views

urlpatterns = [
    path('send/<int:patient_id>/', views.send_questionnaire_and_history, name='send_questionnaire_and_history'),
    path('my/', views.patient_questionnaires, name='patient_questionnaires'),
    path('fill/<int:request_id>/', views.fill_questionnaire, name='fill_questionnaire'),

]
