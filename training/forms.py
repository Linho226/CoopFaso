from django import forms

from .models import Course


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = (
            'title', 'theme', 'summary', 'content',
            'cover_image', 'document', 'video_file', 'video_url', 'is_published',
        )
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 10}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class QuizQuestionCreateForm(forms.Form):
    question = forms.CharField(
        label='Question',
        max_length=500,
        widget=forms.Textarea(attrs={'rows': 2}),
    )
    choice_1 = forms.CharField(label='Reponse 1', max_length=300)
    choice_2 = forms.CharField(label='Reponse 2', max_length=300)
    choice_3 = forms.CharField(label='Reponse 3', max_length=300, required=False)
    choice_4 = forms.CharField(label='Reponse 4', max_length=300, required=False)
    correct_choice = forms.ChoiceField(
        label='Bonne reponse',
        choices=(
            ('1', 'Reponse 1'),
            ('2', 'Reponse 2'),
            ('3', 'Reponse 3'),
            ('4', 'Reponse 4'),
        ),
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'correct_choice':
                field.widget.attrs['class'] = 'quiz-radio-list'
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        choices = [
            cleaned_data.get('choice_1', '').strip(),
            cleaned_data.get('choice_2', '').strip(),
            cleaned_data.get('choice_3', '').strip(),
            cleaned_data.get('choice_4', '').strip(),
        ]
        filled_choices = [choice for choice in choices if choice]
        if len(filled_choices) < 2:
            raise forms.ValidationError('Ajoutez au moins deux reponses.')

        correct_index = int(cleaned_data.get('correct_choice') or 0) - 1
        if correct_index < 0 or correct_index >= len(choices) or not choices[correct_index]:
            raise forms.ValidationError('La bonne reponse doit correspondre a une reponse remplie.')

        return cleaned_data

    @property
    def choices_payload(self):
        correct_index = int(self.cleaned_data['correct_choice'])
        payload = []
        for index in range(1, 5):
            text = self.cleaned_data.get(f'choice_{index}', '').strip()
            if text:
                payload.append({
                    'text': text,
                    'is_correct': index == correct_index,
                })
        return payload
