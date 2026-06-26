from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cooperatives.models import Cooperative
from products.models import Product, ProductCategory
from training.models import (
    Course,
    CourseProgress,
    QuizAttempt,
    QuizChoice,
    QuizProgress,
    QuizQuestion,
)

from .models import ContactMessage, News


class PublicSiteTests(TestCase):
    def setUp(self):
        self.cooperative = Cooperative.objects.create(
            name='Cooperative Publique',
            address='Koudougou',
            phone='+22670000000',
            email='publique@coop.bf',
            region='Centre-Ouest',
            province='Boulkiemde',
            creation_date=date(2020, 1, 1),
            description='Une cooperative engagee.',
        )
        self.category = ProductCategory.objects.create(name='Test public')
        self.product = Product.objects.create(
            cooperative=self.cooperative,
            category=self.category,
            name='Tomate locale',
            description='Tomates fraiches',
            price=Decimal('750.00'),
            quantity_available=Decimal('25.00'),
        )
        self.hidden_product = Product.objects.create(
            cooperative=self.cooperative,
            category=self.category,
            name='Produit masque',
            price=Decimal('100.00'),
            quantity_available=Decimal('10.00'),
            is_published=False,
        )
        author = User.objects.create_user(username='formateur')
        self.course = Course.objects.create(
            title='Formation publique',
            theme=Course.Theme.IRRIGATION,
            summary='Apprendre a irriguer.',
            content='Contenu public',
            author=author,
            is_published=True,
        )
        self.question = QuizQuestion.objects.create(
            course=self.course,
            text='Quel outil economise l eau ?',
        )
        self.correct_choice = QuizChoice.objects.create(
            question=self.question,
            text='Le goutte a goutte',
            is_correct=True,
        )
        QuizChoice.objects.create(
            question=self.question,
            text='L arrosage a midi',
            is_correct=False,
        )
        self.news = News.objects.create(
            title='Actualite publique',
            summary='Une actualite agricole.',
            content='Contenu de l actualite.',
            published_at=timezone.now(),
        )

    def test_public_pages_are_accessible_without_login(self):
        urls = (
            reverse('public_site:home'),
            reverse('public_site:products'),
            reverse('public_site:product_detail', args=[self.product.pk]),
            reverse('public_site:cooperatives'),
            reverse('public_site:cooperative_detail', args=[self.cooperative.pk]),
            reverse('public_site:trainings'),
            reverse('public_site:training_detail', args=[self.course.pk]),
            reverse('public_site:news'),
            reverse('public_site:news_detail', args=[self.news.pk]),
            reverse('public_site:contact'),
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_catalogue_filters_and_hides_unpublished_products(self):
        response = self.client.get(reverse('public_site:products'), {
            'category': self.category.pk,
            'region': 'Centre-Ouest',
            'q': 'Tomate',
        })
        self.assertContains(response, 'Tomate locale')
        self.assertNotContains(response, 'Produit masque')

    def test_contact_form_creates_admin_message(self):
        response = self.client.post(reverse('public_site:contact'), {
            'category': ContactMessage.Category.PARTNERSHIP,
            'name': 'Awa Test',
            'email': 'awa@example.com',
            'phone': '+22670000001',
            'subject': 'Partenariat',
            'message': 'Je souhaite rejoindre la plateforme.',
        })
        self.assertRedirects(response, reverse('public_site:contact'))
        self.assertTrue(ContactMessage.objects.filter(email='awa@example.com').exists())

    def test_authenticated_contact_message_is_linked_to_sender(self):
        buyer = User.objects.create_user(
            username='buyer_message',
            password='Password123!',
            email='buyer@example.com',
        )
        self.client.force_login(buyer)

        self.client.post(reverse('public_site:contact'), {
            'category': ContactMessage.Category.ROLE_REQUEST,
            'name': 'Buyer Message',
            'email': buyer.email,
            'phone': '+22670000002',
            'subject': 'Demande de role agriculteur',
            'message': 'Je souhaite devenir agriculteur.',
        })

        contact_message = ContactMessage.objects.get(subject='Demande de role agriculteur')
        self.assertEqual(contact_message.sender, buyer)

    def test_hidden_product_is_not_publicly_accessible(self):
        response = self.client.get(
            reverse('public_site:product_detail', args=[self.hidden_product.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_public_training_detail_shows_quiz_for_authenticated_user(self):
        user = User.objects.create_user(username='public_learner')
        self.client.force_login(user)

        response = self.client.get(
            reverse('public_site:training_detail', args=[self.course.pk])
        )

        self.assertContains(response, 'Testez vos connaissances')
        self.assertContains(response, 'Quel outil economise l eau ?')
        self.assertContains(response, 'Demarrer le quiz')
        self.assertContains(response, 'courseQuizDialog')
        self.assertContains(response, 'Valider mes reponses')

    def test_public_training_quiz_submit_records_score(self):
        user = User.objects.create_user(username='public_quiz_user')
        self.client.force_login(user)

        response = self.client.post(
            reverse('public_site:training_quiz_submit', args=[self.course.pk]),
            {f'question_{self.question.pk}': self.correct_choice.pk},
        )

        self.assertRedirects(
            response,
            reverse('public_site:training_detail', args=[self.course.pk]),
        )
        attempt = QuizAttempt.objects.get(user=user, course=self.course)
        self.assertEqual(attempt.score, 1)

    def test_public_quiz_requires_video_completion_when_course_has_video(self):
        self.course.video_url = 'https://example.com/video.mp4'
        self.course.save(update_fields=['video_url'])
        user = User.objects.create_user(username='public_locked_quiz_user')
        self.client.force_login(user)

        detail_response = self.client.get(
            reverse('public_site:training_detail', args=[self.course.pk])
        )
        self.assertContains(detail_response, 'Regardez la video')

        response = self.client.post(
            reverse('public_site:training_quiz_submit', args=[self.course.pk]),
            {f'question_{self.question.pk}': self.correct_choice.pk},
        )

        self.assertRedirects(
            response,
            reverse('public_site:training_detail', args=[self.course.pk]),
        )
        self.assertFalse(QuizAttempt.objects.filter(user=user, course=self.course).exists())

    def test_public_video_completion_unlocks_quiz(self):
        self.course.video_url = 'https://example.com/video.mp4'
        self.course.save(update_fields=['video_url'])
        user = User.objects.create_user(username='public_video_done_user')
        self.client.force_login(user)

        response = self.client.post(
            reverse('public_site:training_video_complete', args=[self.course.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            CourseProgress.objects.get(user=user, course=self.course).video_completed
        )

    def test_public_quiz_progress_is_saved(self):
        user = User.objects.create_user(username='public_quiz_pause_user')
        self.client.force_login(user)

        response = self.client.post(
            reverse('public_site:training_quiz_progress', args=[self.course.pk]),
            data='{"current_index": 0, "answers": {"%s": "%s"}}' % (
                self.question.pk,
                self.correct_choice.pk,
            ),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        progress = QuizProgress.objects.get(user=user, course=self.course)
        self.assertEqual(progress.answers[str(self.question.pk)], str(self.correct_choice.pk))
        self.assertEqual(progress.current_index, 0)

    def test_completed_public_quiz_cannot_be_reopened_or_resubmitted(self):
        user = User.objects.create_user(username='public_completed_quiz_user')
        QuizAttempt.objects.create(
            user=user,
            course=self.course,
            score=1,
            total=1,
        )
        self.client.force_login(user)

        detail_response = self.client.get(
            reverse('public_site:training_detail', args=[self.course.pk])
        )
        self.assertContains(detail_response, 'Quiz termine')
        self.assertNotContains(detail_response, 'Demarrer le quiz')

        response = self.client.post(
            reverse('public_site:training_quiz_submit', args=[self.course.pk]),
            {f'question_{self.question.pk}': self.correct_choice.pk},
        )

        self.assertRedirects(
            response,
            reverse('public_site:training_detail', args=[self.course.pk]),
        )
        self.assertEqual(QuizAttempt.objects.filter(user=user, course=self.course).count(), 1)


class NewsManagementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='news_admin',
            password='Password123!',
            is_staff=True,
        )
        self.buyer = User.objects.create_user(
            username='news_buyer',
            password='Password123!',
        )

    def news_payload(self, **overrides):
        payload = {
            'title': 'Nouvelle recolte nationale',
            'summary': 'Une information importante pour les producteurs.',
            'content': 'Contenu complet de l actualite agricole.',
            'published_at': timezone.localtime().strftime('%Y-%m-%dT%H:%M'),
            'is_published': 'on',
        }
        payload.update(overrides)
        return payload

    def test_admin_can_create_update_and_delete_news(self):
        self.client.force_login(self.admin)

        create_response = self.client.post(
            reverse('public_site:news_manage_create'),
            self.news_payload(),
        )
        news = News.objects.get(title='Nouvelle recolte nationale')
        self.assertRedirects(
            create_response,
            reverse('public_site:news_manage_update', args=[news.pk]),
        )

        update_response = self.client.post(
            reverse('public_site:news_manage_update', args=[news.pk]),
            self.news_payload(title='Recolte nationale mise a jour'),
        )
        self.assertRedirects(
            update_response,
            reverse('public_site:news_manage_update', args=[news.pk]),
        )
        news.refresh_from_db()
        self.assertEqual(news.title, 'Recolte nationale mise a jour')

        delete_response = self.client.post(
            reverse('public_site:news_manage_delete', args=[news.pk])
        )
        self.assertRedirects(
            delete_response,
            reverse('public_site:news_manage_list'),
        )
        self.assertFalse(News.objects.filter(pk=news.pk).exists())

    def test_non_admin_cannot_access_news_management(self):
        self.client.force_login(self.buyer)

        response = self.client.get(reverse('public_site:news_manage_list'))

        self.assertEqual(response.status_code, 302)

    def test_unpublished_news_is_not_publicly_accessible(self):
        news = News.objects.create(
            title='Brouillon prive',
            summary='Resume',
            content='Contenu',
            published_at=timezone.now(),
            is_published=False,
        )

        response = self.client.get(
            reverse('public_site:news_detail', args=[news.pk])
        )

        self.assertEqual(response.status_code, 404)
