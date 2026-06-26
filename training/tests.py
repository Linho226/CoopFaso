from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserProfile

from .models import Course, QuizAttempt, QuizChoice, QuizQuestion


class TrainingTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username='trainer',
            password='Password123!',
        )
        self.manager.profile.role = UserProfile.Role.COOPERATIVE_MANAGER
        self.manager.profile.save()
        self.admin = User.objects.create_user(
            username='training_admin',
            password='Password123!',
            is_staff=True,
        )
        self.farmer = User.objects.create_user(
            username='learner',
            password='Password123!',
        )
        self.course = Course.objects.create(
            title='Irrigation goutte a goutte',
            theme=Course.Theme.IRRIGATION,
            summary='Economiser l’eau.',
            content='Contenu du cours',
            author=self.manager,
            is_published=True,
        )
        self.question = QuizQuestion.objects.create(
            course=self.course,
            text='Quel systeme economise le plus d’eau ?',
        )
        self.correct_choice = QuizChoice.objects.create(
            question=self.question,
            text='Le goutte a goutte',
            is_correct=True,
        )
        QuizChoice.objects.create(
            question=self.question,
            text='L’inondation permanente',
            is_correct=False,
        )

    def test_authenticated_user_can_view_course(self):
        self.client.force_login(self.farmer)
        response = self.client.get(
            reverse('training:detail', args=[self.course.pk])
        )
        self.assertContains(response, 'Irrigation goutte a goutte')
        self.assertContains(response, 'Quiz')

    def test_admin_can_publish_course(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('training:create'), {
            'title': 'Fertilisation organique',
            'theme': Course.Theme.FERTILIZATION,
            'summary': 'Comprendre le compost.',
            'content': 'Un cours complet.',
            'video_url': '',
            'is_published': 'on',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Course.objects.filter(title='Fertilisation organique').exists()
        )

    def test_farmer_cannot_publish_course(self):
        self.client.force_login(self.farmer)
        response = self.client.get(reverse('training:create'))
        self.assertEqual(response.status_code, 302)

    def test_manager_cannot_publish_course(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse('training:create'))
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_quiz_score_is_recorded(self):
        self.client.force_login(self.farmer)
        response = self.client.post(
            reverse('training:quiz_submit', args=[self.course.pk]),
            {f'question_{self.question.pk}': self.correct_choice.pk},
        )
        self.assertRedirects(response, self.course.get_absolute_url())
        attempt = QuizAttempt.objects.get(user=self.farmer, course=self.course)
        self.assertEqual(attempt.score, 1)
        self.assertEqual(attempt.percentage, 100)
