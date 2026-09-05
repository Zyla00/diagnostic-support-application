from django.urls import path
from .views import (
    CustomLoginView,
    CustomLogoutView,
    RegisterView,
    CustomPasswordChangeView,
    profile_view,
    profile_edit,
    edit_settings,
    patient_dashboard_view,
    specialist_dashboard_view,
)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('edit-password/', CustomPasswordChangeView.as_view(), name='edit-password'),

    # Profil
    path('profile/', profile_view, name='profile-view'),

    path('profile/edit/', profile_edit, name='profile-edit'),

    # Ustawienia
    path('settings/edit/', edit_settings, name='edit_settings'),

    # Dashboardy
    path('dashboard/patient/', patient_dashboard_view, name='patient-dashboard'),
    path('dashboard/specialist/', specialist_dashboard_view, name='specialist-dashboard'),
]
