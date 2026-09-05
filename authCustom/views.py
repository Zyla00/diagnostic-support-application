from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic.edit import FormView
from .forms import UserUpdateForm


from .forms import (
    SignInForm,
    UserRegistrationForm,
    CustomPasswordChangeForm,
    SettingsForm,
    PatientProfileForm,
    SpecialistProfileForm
)
from .models import PatientProfile, SpecialistProfile


class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    form_class = SignInForm

    def get_success_url(self):
        next_url = self.request.GET.get('next') or '/'
        if not url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={self.request.get_host()},
                require_https=self.request.is_secure()):
            next_url = '/'
        return next_url

    def form_valid(self, form):
        super().form_valid(form)
        if not form.cleaned_data.get('remember_me'):
            self.request.session.set_expiry(0)
        else:
            self.request.session.set_expiry(1209600)
        return JsonResponse({'success': True, 'redirect_url': self.get_success_url()})

    def form_invalid(self, form):
        errors = {
            str(form.fields.get(field_name, field_name).label or field_name): [
                str(msg) for msg in messages
            ] for field_name, messages in form.errors.items()
        }
        return JsonResponse({'success': False, 'errors': errors}, status=400)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('redirect-by-role')


class RegisterView(FormView):
    template_name = 'auth/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('redirect-by-role')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return JsonResponse({'success': True, 'redirect_url': self.get_success_url()})

    def form_invalid(self, form):
        errors = {
            str(form.fields.get(field_name, field_name).label or field_name): [
                str(msg) for msg in messages
            ] for field_name, messages in form.errors.items()
        }
        return JsonResponse({'success': False, 'errors': errors}, status=400)


class CustomPasswordChangeView(FormView):
    template_name = 'auth/edit_password.html'
    form_class = CustomPasswordChangeForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return JsonResponse({'success': True, 'username': request.user.username})
        else:
            errors = {
                str(form.fields.get(field_name, field_name).label or field_name): [
                    str(msg) for msg in messages
                ] for field_name, messages in form.errors.items()
            }
            return JsonResponse({'success': False, 'errors': errors})


@login_required
def edit_settings(request):
    form = SettingsForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        return HttpResponse(status=204)

    html = render_to_string("auth/settings_form.html", {"form": form}, request=request)
    return HttpResponse(html)


@login_required
def redirect_by_role_view(request):
    user = request.user
    if user.role == 'patient':
        return redirect('patient-dashboard')
    elif user.role == 'specialist':
        return redirect('specialist-dashboard')
    return redirect('login')


# @login_required
# def patient_dashboard_view(request):
#     return render(request, 'dashboard/patient.html')
#
#
# @login_required
# def specialist_dashboard_view(request):
#     return render(request, 'dashboard/specialist.html')


from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

@login_required
def patient_dashboard_view(request):
    return redirect('my_recommendations')

@login_required
def specialist_dashboard_view(request):
    return redirect('my_patients')


@login_required
def profile_view(request):
    user = request.user

    # Pobieramy odpowiedni profil użytkownika
    profile = (
        getattr(user, 'patientprofile', None)
        if user.role == 'patient'
        else getattr(user, 'specialistprofile', None)
    )

    return render(request, 'auth/profile_view.html', {
        'user': user,
        'profile': profile,
    })


@login_required
def profile_edit(request):
    user = request.user

    if user.role == 'patient':
        profile, _ = PatientProfile.objects.get_or_create(user=user)
        profile_form_class = PatientProfileForm
        template_name = 'auth/profile_edit_patient.html'
    else:
        profile, _ = SpecialistProfile.objects.get_or_create(user=user)
        profile_form_class = SpecialistProfileForm
        template_name = 'auth/profile_edit_specialist.html'

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = profile_form_class(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return JsonResponse({'success': True})
        else:
            errors = {**user_form.errors, **profile_form.errors}
            print("FORMULARZ BŁĘDY:", errors)  # DEBUG: możesz usunąć po testach
            return JsonResponse({'success': False, 'errors': errors}, status=400)

    # GET – renderujemy formularz
    user_form = UserUpdateForm(instance=user)
    profile_form = profile_form_class(instance=profile)

    html = render_to_string(
        template_name,
        {'user_form': user_form, 'profile_form': profile_form},
        request=request
    )
    return HttpResponse(html)

