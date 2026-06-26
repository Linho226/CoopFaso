from urllib.parse import parse_qs, urlparse

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
    cover_image = models.ImageField(
        'affiche',
        upload_to='training/covers/',
        blank=True,
        null=True,
    )
    document = models.FileField(
        'document',
        upload_to='training/documents/',
        blank=True,
        null=True,
    )
    video_file = models.FileField(
        'fichier video',
        upload_to='training/videos/',
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

    @property
    def has_video(self):
        return bool(self.video_file or self.video_url)

    @property
    def video_embed_url(self):
        if not self.video_url:
            return ''
        video_id = self.youtube_video_id
        if video_id:
            return (
                f'https://www.youtube.com/embed/{video_id}'
                '?rel=0&modestbranding=1&playsinline=1&enablejsapi=1'
            )

        parsed = self.parsed_video_url
        host = self.video_host
        path_parts = self.video_path_parts

        if host in {'vimeo.com', 'player.vimeo.com'} and path_parts and path_parts[-1].isdigit():
            return f'https://player.vimeo.com/video/{path_parts[-1]}'

        return ''

    @property
    def parsed_video_url(self):
        return urlparse(self.video_url.strip()) if self.video_url else urlparse('')

    @property
    def video_host(self):
        return self.parsed_video_url.netloc.lower().removeprefix('www.')

    @property
    def video_path_parts(self):
        return [part for part in self.parsed_video_url.path.split('/') if part]

    @property
    def youtube_video_id(self):
        if not self.video_url:
            return ''
        host = self.video_host
        path_parts = self.video_path_parts

        if host in {'youtube.com', 'm.youtube.com'}:
            if path_parts[:1] == ['embed'] and len(path_parts) > 1:
                return path_parts[1]
            if path_parts[:1] == ['shorts'] and len(path_parts) > 1:
                return path_parts[1]
            return parse_qs(self.parsed_video_url.query).get('v', [''])[0]

        if host == 'youtu.be' and path_parts:
            return path_parts[0]

        return ''

    @property
    def video_thumbnail_url(self):
        video_id = self.youtube_video_id
        return f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg' if video_id else ''

    @property
    def video_platform_name(self):
        host = self.video_host
        if 'youtube' in host or host == 'youtu.be':
            return 'YouTube'
        if 'vimeo' in host:
            return 'Vimeo'
        return 'la plateforme video'

    @property
    def video_url_is_direct_file(self):
        if not self.video_url:
            return False
        return urlparse(self.video_url).path.lower().endswith((
            '.mp4',
            '.webm',
            '.ogg',
        ))


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


class CourseProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_progress',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='progress_records',
    )
    video_completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'course'),
                name='unique_course_progress_per_user',
            ),
        ]
        verbose_name = 'progression de cours'
        verbose_name_plural = 'progressions de cours'


class QuizProgress(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'En cours'
        COMPLETED = 'COMPLETED', 'Termine'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_progress',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='quiz_progress_records',
    )
    answers = models.JSONField(default=dict, blank=True)
    current_index = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )
    score = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'course'),
                name='unique_quiz_progress_per_user',
            ),
        ]
        verbose_name = 'progression de quiz'
        verbose_name_plural = 'progressions de quiz'

    @property
    def percentage(self):
        return round((self.score / self.total) * 100) if self.total else 0
