from django.conf import settings
from django.db import models
from django.urls import reverse


class Course(models.Model):
    class Theme(models.TextChoices):
        SUSTAINABLE = 'SUSTAINABLE', 'Agriculture durable'
        FERTILIZATION = 'FERTILIZATION', 'Fertilisation'
        IRRIGATION = 'IRRIGATION', 'Irrigation'
        PESTS = 'PESTS', 'Gestion des ravageurs'
        HARVEST = 'HARVEST', 'Techniques de recolte'

    title = models.CharField('titre', max_length=180)
    theme = models.CharField('theme', max_length=24, choices=Theme.choices)
    summary = models.TextField('resume')
    content = models.TextField('contenu du cours')
    document = models.FileField(
        'document',
        upload_to='training/documents/',
        blank=True,
        null=True,
    )
    video_url = models.URLField('lien de la video', blank=True)
    is_published = models.BooleanField('publie', default=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='courses',
        verbose_name='auteur',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('theme', 'title')
        verbose_name = 'cours'
        verbose_name_plural = 'cours'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('training:detail', kwargs={'pk': self.pk})


class QuizQuestion(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='cours',
    )
    text = models.CharField('question', max_length=500)
    order = models.PositiveIntegerField('ordre', default=0)

    class Meta:
        ordering = ('order', 'id')
        verbose_name = 'question de quiz'
        verbose_name_plural = 'questions de quiz'

    def __str__(self):
        return self.text


class QuizChoice(models.Model):
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name='choices',
        verbose_name='question',
    )
    text = models.CharField('reponse', max_length=300)
    is_correct = models.BooleanField('bonne reponse', default=False)

    class Meta:
        ordering = ('id',)
        verbose_name = 'choix de reponse'
        verbose_name_plural = 'choix de reponse'

    def __str__(self):
        return self.text


class QuizAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='attempts',
    )
    score = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-completed_at',)
        verbose_name = 'tentative de quiz'
        verbose_name_plural = 'tentatives de quiz'

    @property
    def percentage(self):
        return round((self.score / self.total) * 100) if self.total else 0
