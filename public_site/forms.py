from django import forms
from django.utils import timezone

from .models import ContactMessage, News


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ('category', 'name', 'email', 'phone', 'subject', 'message')
        labels = {
            'category': 'Motif',
            'name': 'Nom',
            'email': 'Email',
            'phone': 'Telephone',
            'subject': 'Objet',
            'message': 'Message',
        }
        widgets = {
            'category': forms.Select(),
            'name': forms.TextInput(attrs={'placeholder': 'Votre nom complet'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Votre adresse email'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Votre numero de telephone'}),
            'subject': forms.TextInput(attrs={'placeholder': 'Objet de votre message'}),
            'message': forms.Textarea(attrs={'placeholder': 'Expliquez votre demande...'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated and not self.is_bound:
            self.initial.update({
                'name': user.get_full_name() or user.username,
                'email': user.email,
                'phone': getattr(user.profile, 'phone', ''),
            })


class ContactReplyForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ('status', 'admin_reply')
        labels = {
            'status': 'Statut',
            'admin_reply': 'Reponse au client',
        }
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'admin_reply': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Saisissez votre reponse...',
            }),
        }


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = (
            'title',
            'summary',
            'content',
            'image',
            'published_at',
            'is_published',
        )
        labels = {
            'title': 'Titre',
            'summary': 'Resume',
            'content': 'Contenu',
            'image': 'Image',
            'published_at': 'Date de publication',
            'is_published': 'Publier sur le site',
        }
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 10}),
            'published_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['published_at'].input_formats = ('%Y-%m-%dT%H:%M',)
        if not self.is_bound and not self.instance.pk:
            self.fields['published_at'].initial = timezone.localtime().strftime(
                '%Y-%m-%dT%H:%M'
            )
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-check-input')
            else:
                field.widget.attrs.setdefault('class', 'form-control')
