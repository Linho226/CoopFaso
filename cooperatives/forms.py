from django import forms
from django.contrib.auth.models import User

from accounts.models import UserProfile

from .models import Cooperative


class CooperativeForm(forms.ModelForm):
    manager = forms.ModelChoiceField(
        label='Responsable de la cooperative',
        queryset=User.objects.none(),
        required=True,
        help_text=(
            'Selectionnez un compte existant. Il deviendra responsable '
            'de cette cooperative.'
        ),
    )

    class Meta:
        model = Cooperative
        fields = (
            'name',
            'address',
            'phone',
            'email',
            'region',
            'province',
            'creation_date',
            'description',
            'logo',
            'is_public',
        )
        labels = {
            'name': 'Nom',
            'address': 'Adresse',
            'phone': 'Telephone',
            'email': 'Email',
            'region': 'Region',
            'province': 'Province',
            'creation_date': 'Date de creation',
            'description': 'Presentation',
            'logo': 'Logo',
            'is_public': 'Visible sur le site public',
        }
        widgets = {
            'creation_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        allow_manager_assignment = kwargs.pop('allow_manager_assignment', True)
        super().__init__(*args, **kwargs)
        current_manager = None
        if self.instance and self.instance.pk:
            current_manager = User.objects.filter(
                profile__role=UserProfile.Role.COOPERATIVE_MANAGER,
                profile__cooperative=self.instance,
            ).first()
        available_users = User.objects.filter(
            is_superuser=False,
            is_staff=False,
        ).exclude(
            profile__role=UserProfile.Role.COOPERATIVE_MANAGER,
            profile__cooperative__isnull=False,
        )
        if current_manager:
            available_users = available_users | User.objects.filter(
                pk=current_manager.pk
            )
            self.fields['manager'].initial = current_manager
        self.fields['manager'].queryset = available_users.distinct().order_by(
            'first_name', 'last_name', 'username'
        )
        if not allow_manager_assignment:
            self.fields.pop('manager')
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                css_class = 'form-select'
            elif isinstance(field.widget, forms.CheckboxInput):
                css_class = 'form-check-input'
            else:
                css_class = 'form-control'
            field.widget.attrs.setdefault('class', css_class)
