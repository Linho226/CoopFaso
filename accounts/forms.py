from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.contrib.auth.models import User

from .models import UserProfile


class SignUpForm(UserCreationForm):
    allowed_roles = (
        (UserProfile.Role.COOPERATIVE_MANAGER, 'Responsable de cooperative'),
        (UserProfile.Role.FARMER, 'Agriculteur'),
        (UserProfile.Role.BUYER, 'Acheteur'),
    )

    first_name = forms.CharField(label='Prenom', max_length=150)
    last_name = forms.CharField(label='Nom', max_length=150)
    email = forms.EmailField(label='Email')
    phone = forms.CharField(label='Telephone', max_length=30, required=False)
    role = forms.ChoiceField(label='Role', choices=allowed_roles)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'phone',
            'role',
            'password1',
            'password2',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['username'].label = "Nom d'utilisateur"
        self.fields['password1'].label = 'Mot de passe'
        self.fields['password2'].label = 'Confirmation'
        self.fields['role'].widget.attrs['class'] = 'form-select'

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Un compte utilise deja cette adresse email.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data['role']
            profile.phone = self.cleaned_data['phone']
            profile.save()
        return user


class RoleUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('role',)
        labels = {'role': 'Role'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].widget.attrs.setdefault('class', 'form-select')


class StyledAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Nom d'utilisateur")
    password = forms.CharField(label='Mot de passe', widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control form-control-lg')


class StyledPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label='Adresse email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'nom@example.com',
        })


class StyledSetPasswordForm(SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields['new_password1'].label = 'Nouveau mot de passe'
        self.fields['new_password2'].label = 'Confirmation'
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control form-control-lg')
