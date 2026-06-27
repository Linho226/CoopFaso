from django import forms
from django.utils import timezone
from .models import Production
from members.models import Member
from products.models import Product

class ProductionForm(forms.ModelForm):
    class Meta:
        model = Production
        fields = (
            'member',
            'product',
            'quantity',
            'harvest_date',
            'estimated_price',
        )
        labels = {
            'member': 'Membre',
            'product': 'Produit',
            'quantity': 'Quantite recoltee',
            'harvest_date': 'Date de recolte',
            'estimated_price': 'Prix estimatif (FCFA, optionnel)',
        }
        widgets = {
            'harvest_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        cooperative = kwargs.pop('cooperative', None)
        super().__init__(*args, **kwargs)
        if cooperative:
            self.fields['member'].queryset = Member.objects.filter(cooperative=cooperative)
            self.fields['product'].queryset = Product.objects.filter(cooperative=cooperative)
        self.fields['harvest_date'].initial = (
            self.instance.harvest_date
            if self.instance and self.instance.pk
            else timezone.localdate()
        )
        
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')

    def clean(self):
        cleaned_data = super().clean()
        member = cleaned_data.get('member')
        product = cleaned_data.get('product')
        if member and product and member.cooperative_id != product.cooperative_id:
            raise forms.ValidationError(
                'Le membre et le produit doivent appartenir a la meme cooperative.'
            )
        return cleaned_data

class FarmerProductionForm(forms.ModelForm):
    class Meta:
        model = Production
        fields = (
            'product',
            'quantity',
            'harvest_date',
        )
        labels = {
            'product': 'Produit',
            'quantity': 'Quantite recoltee',
            'harvest_date': 'Date de recolte',
        }
        widgets = {
            'harvest_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        cooperative = kwargs.pop('cooperative', None)
        super().__init__(*args, **kwargs)
        if cooperative:
            self.fields['product'].queryset = Product.objects.filter(cooperative=cooperative)
        self.fields['harvest_date'].initial = (
            self.instance.harvest_date
            if self.instance and self.instance.pk
            else timezone.localdate()
        )
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')
