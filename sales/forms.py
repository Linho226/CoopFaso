from django import forms


class CartAddForm(forms.Form):
    quantity = forms.IntegerField(label='Quantite', min_value=1, initial=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quantity'].widget.attrs.update({
            'class': 'form-control',
            'inputmode': 'numeric',
        })


class CheckoutForm(forms.Form):
    delivery_address = forms.CharField(
        label='Adresse de livraison',
        max_length=255,
    )
    phone = forms.CharField(label='Telephone', max_length=30)
    notes = forms.CharField(
        label='Instructions complementaires',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and not self.is_bound:
            self.fields['phone'].initial = getattr(
                getattr(user, 'profile', None),
                'phone',
                '',
            )
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
