from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from .models import CustomUser, SpecialistProfile, PatientProfile


class SignInForm(AuthenticationForm):
    remember_me = forms.BooleanField(label='Zapamiętaj mnie', required=False, initial=False)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError('Nazwa użytkownika nie może być pusta.')
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            raise ValidationError('Hasło nie może być puste.')
        return password


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        widget=forms.RadioSelect,
        label="Rola"
    )
    license_number = forms.CharField(
        required=False,
        label="Numer PWZ (tylko dla specjalistów)"
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'role']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if '@' not in email:
            raise ValidationError('Podaj poprawny adres e-mail.')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('Ten adres e-mail jest już zajęty.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        license_number = cleaned_data.get('license_number')

        if role == 'specialist' and not license_number:
            self.add_error('license_number', 'Numer PWZ jest wymagany dla specjalistów.')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']

        if commit:
            user.save()

            if user.role == 'specialist':
                SpecialistProfile.objects.create(
                    user=user,
                    license_number=self.cleaned_data.get('license_number')
                )
            else:
                return user


        return user


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='Stare hasło',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Stare hasło'})
    )
    new_password1 = forms.CharField(
        label='Nowe hasło',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nowe hasło'})
    )
    new_password2 = forms.CharField(
        label='Potwierdź nowe hasło',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Potwierdź nowe hasło'})
    )


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "email", "phone"]
        widgets = {
            "phone": forms.TextInput(attrs={"placeholder": "+48 123-456-789"}),
        }
        labels = {
            'phone': 'Telefon',
        }


class PatientProfileForm(forms.ModelForm):
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Data urodzenia",
    )

    class Meta:
        model = PatientProfile
        fields = [
            "birth_date",
            "pesel",
            "insurance",
        ]
        widgets = {
            "pesel": forms.TextInput(attrs={"maxlength": 11, "pattern": r"\d{11}"}),
        }


class SpecialistProfileForm(forms.ModelForm):
    class Meta:
        model = SpecialistProfile
        fields = [
            "second_name",
            "photo",
            "specialization",
            "education",
            "experience",
            "license_number",
            "location",
            "description",
            "phone",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }



class SettingsForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["email", "first_name", "last_name"]
