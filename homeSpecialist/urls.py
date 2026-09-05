# patient/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.specialist_dashboard, name='specialist_dashboard'),
]
