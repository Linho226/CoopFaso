from django import forms

from .models import Cooperative


class CooperativeForm(forms.ModelForm):
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
        )
        labels = {
            'name': 'Nom',
            'address': 'Adresse',
            'phone': 'Telephone',
            'email': 'Email',
            'region': 'Region',
            'province': 'Province',
            'creation_date': 'Date de creation',
        }
        widgets = {
            'creation_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css_class)
