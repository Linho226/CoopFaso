from django import forms

from .models import Member


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = (
            'last_name',
            'first_name',
            'gender',
            'birth_date',
            'phone',
            'address',
            'photo',
            'cooperative',
        )
        labels = {
            'last_name': 'Nom',
            'first_name': 'Prenom',
            'gender': 'Sexe',
            'birth_date': 'Date de naissance',
            'phone': 'Telephone',
            'address': 'Adresse',
            'photo': 'Photo',
            'cooperative': 'Cooperative',
        }
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')
            elif isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs.setdefault('class', 'form-control')
            else:
                field.widget.attrs.setdefault('class', 'form-control')
