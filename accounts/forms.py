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
    first_name = forms.CharField(label='Prenom', max_length=150)
    last_name = forms.CharField(label='Nom', max_length=150)
    email = forms.EmailField(label='Email')
    phone = forms.CharField(label='Telephone', max_length=30, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'phone',
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
            profile.role = UserProfile.Role.BUYER
            profile.phone = self.cleaned_data['phone']
            profile.cooperative = None
            profile.save(update_fields=['role', 'phone', 'cooperative', 'updated_at'])
        return user


class RoleUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('role', 'cooperative')
        labels = {
            'role': 'Role',
            'cooperative': 'Cooperative rattachee',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-select')

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        cooperative = cleaned_data.get('cooperative')
        if role == UserProfile.Role.COOPERATIVE_MANAGER:
            if not cooperative:
                self.add_error(
                    'cooperative',
                    'Selectionnez la cooperative geree par ce responsable.',
                )
            elif UserProfile.objects.filter(
                role=UserProfile.Role.COOPERATIVE_MANAGER,
                cooperative=cooperative,
            ).exclude(pk=self.instance.pk).exists():
                self.add_error(
                    'cooperative',
                    'Cette cooperative possede deja un responsable.',
                )
        return cleaned_data


class ProfileForm(forms.Form):
    first_name = forms.CharField(label='Prenom', max_length=150)
    last_name = forms.CharField(label='Nom', max_length=150)
    email = forms.EmailField(label='Email')
    phone = forms.CharField(label='Telephone', max_length=30, required=False)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user and not self.is_bound:
            self.initial.update({
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': getattr(user.profile, 'phone', ''),
            })
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def save(self):
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.email = self.cleaned_data['email']
        self.user.save(update_fields=['first_name', 'last_name', 'email'])
        self.user.profile.phone = self.cleaned_data['phone']
        self.user.profile.save(update_fields=['phone', 'updated_at'])
        return self.user


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
