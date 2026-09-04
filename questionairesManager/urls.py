from django.urls import path
from . import views

app_name = 'questionairesManager'

urlpatterns = [
    path('', views.questionnaire_list, name='questionnaire_list'),
    path('create/', views.create_questionnaire, name='create_questionnaire'),
    path('<int:pk>/', views.questionnaire_detail, name='questionnaire_detail'),
    path('<int:pk>/edit/', views.edit_questionnaire, name='edit_questionnaire'),
    path('<int:pk>/copy/', views.copy_questionnaire, name='copy_questionnaire'),
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('<int:pk>/delete/', views.delete_questionnaire, name='delete_questionnaire'),
    path('<int:pk>/rename/', views.rename_questionnaire, name='rename_questionnaire'),
    path('ajax/search/', views.search_questionnaires_ajax, name='search_questionnaires_ajax'),
    path('ankiety/<int:questionnaire_id>/section/create/', views.create_section_ajax, name='create_section_ajax'),

]
