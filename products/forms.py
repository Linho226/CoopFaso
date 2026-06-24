from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            'cooperative',
            'name',
            'description',
            'price',
            'quantity_available',
            'image',
        )
        labels = {
            'cooperative': 'Cooperative',
            'name': 'Nom du produit',
            'description': 'Description',
            'price': 'Prix (FCFA)',
            'quantity_available': 'Quantite disponible',
            'image': 'Image',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
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
