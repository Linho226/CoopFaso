from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserProfile

from .forms import CourseForm
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
        self.farmer.profile.role = UserProfile.Role.FARMER
        self.farmer.profile.save()
        self.buyer = User.objects.create_user(
            username='training_buyer',
            password='Password123!',
        )
        self.buyer.profile.role = UserProfile.Role.BUYER
        self.buyer.profile.save()
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

    def test_buyer_can_view_course(self):
        self.client.force_login(self.buyer)
        response = self.client.get(
            reverse('training:detail', args=[self.course.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Irrigation goutte a goutte')

    def test_course_form_accepts_video_file_and_link(self):
        form = CourseForm()

        self.assertIn('cover_image', form.fields)
        self.assertIn('video_file', form.fields)
        self.assertIn('video_url', form.fields)

    def test_course_video_link_is_embedded_on_platform(self):
        self.course.video_url = 'https://www.youtube.com/watch?v=abc123'
        self.course.save(update_fields=['video_url'])
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse('training:detail', args=[self.course.pk])
        )

        self.assertContains(
            response,
            'https://www.youtube.com/embed/abc123',
        )
        self.assertNotContains(response, 'Ouvrir sur YouTube')

    def test_admin_can_manage_quiz_questions(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse('training:quiz_manage', args=[self.course.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nouvelle question')

    def test_admin_course_list_shows_quiz_management_action(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('training:list'))

        self.assertContains(response, 'Quiz · 1')
        self.assertContains(response, 'Gerer le quiz')

    def test_admin_can_add_quiz_question(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse('training:quiz_manage', args=[self.course.pk]),
            {
                'question': 'Quand arroser les plants ?',
                'choice_1': 'Le matin',
                'choice_2': 'A midi',
                'choice_3': '',
                'choice_4': '',
                'correct_choice': '1',
            },
        )

        self.assertRedirects(
            response,
            reverse('training:quiz_manage', args=[self.course.pk]),
        )
        question = QuizQuestion.objects.get(text='Quand arroser les plants ?')
        self.assertEqual(question.choices.count(), 2)
        self.assertEqual(question.choices.get(is_correct=True).text, 'Le matin')

    def test_admin_can_delete_quiz_question(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse('training:quiz_manage', args=[self.course.pk]),
            {
                'action': 'delete_question',
                'question_id': self.question.pk,
            },
        )

        self.assertRedirects(
            response,
            reverse('training:quiz_manage', args=[self.course.pk]),
        )
        self.assertFalse(QuizQuestion.objects.filter(pk=self.question.pk).exists())

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
