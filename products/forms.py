from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            'cooperative',
            'category',
            'name',
            'description',
            'price',
            'quantity_available',
            'unit',
            'image',
            'is_published',
        )
        labels = {
            'cooperative': 'Cooperative',
            'category': 'Categorie',
            'name': 'Nom du produit',
            'description': 'Description',
            'price': 'Prix (FCFA)',
            'quantity_available': 'Quantite disponible',
            'unit': 'Unite',
            'image': 'Image',
            'is_published': 'Visible dans le catalogue public',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        cooperative = kwargs.pop('cooperative', None)
        super().__init__(*args, **kwargs)
        self.fields['unit'].initial = Product.Unit.UNIT
        self.fields['unit'].required = False
        if cooperative:
            self.fields['cooperative'].initial = cooperative
            self.fields['cooperative'].queryset = self.fields[
                'cooperative'
            ].queryset.filter(pk=cooperative.pk)
            self.fields['cooperative'].disabled = True
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-check-input')
            elif isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs.setdefault('class', 'form-control')
            else:
                field.widget.attrs.setdefault('class', 'form-control')

    def clean_unit(self):
        return self.cleaned_data.get('unit') or Product.Unit.UNIT
