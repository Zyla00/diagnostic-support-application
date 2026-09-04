from django.urls import path
from . import views

app_name = 'labTest'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('new/', views.new_survey, name='new_survey'),
    path('result/<int:pk>/', views.result_detail, name='result_detail'),
]
