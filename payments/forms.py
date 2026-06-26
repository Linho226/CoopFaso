from django import forms

from .models import Payment


class PaymentForm(forms.Form):
    method = forms.ChoiceField(label='Mode de paiement', choices=Payment.Method.choices)
    phone = forms.CharField(
        label='Numero Mobile Money',
        max_length=30,
        required=False,
    )
    card_number = forms.CharField(
        label='Numero de carte de simulation',
        max_length=19,
        required=False,
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and not self.is_bound:
            self.fields['phone'].initial = getattr(
                getattr(user, 'profile', None),
                'phone',
                '',
            )
        self.fields['method'].widget.attrs['class'] = 'form-select'
        self.fields['phone'].widget.attrs['class'] = 'form-control'
        self.fields['card_number'].widget.attrs.update({
            'class': 'form-control',
            'inputmode': 'numeric',
            'placeholder': '4242 4242 4242 4242',
        })

    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get('method')
        phone = cleaned_data.get('phone', '').strip()
        card_number = ''.join(filter(str.isdigit, cleaned_data.get('card_number', '')))

        if method in {Payment.Method.ORANGE_MONEY, Payment.Method.WAVE} and not phone:
            self.add_error('phone', 'Indiquez le numero Mobile Money.')
        if method == Payment.Method.CARD and len(card_number) < 12:
            self.add_error('card_number', 'Indiquez un numero de carte de simulation valide.')
        cleaned_data['card_number'] = card_number
        return cleaned_data
