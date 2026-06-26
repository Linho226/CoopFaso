import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cooperatives.models import Cooperative
from members.models import Member
from products.models import Product, ProductCategory
from sales.models import OrderItem
from training.models import Course, CourseProgress, QuizAttempt, QuizProgress

from accounts.access import is_admin

from .forms import ContactForm, NewsForm
from .models import FarmingTip, News, PlatformInfo


def _platform_info():
    return PlatformInfo.objects.first()


def home(request):
    paid_items = OrderItem.objects.filter(order__payment__status='SUCCESS')
    context = {
        'platform': _platform_info(),
        'featured_products': Product.objects.filter(
            is_published=True,
            quantity_available__gt=0,
        ).select_related('cooperative', 'category')[:6],
        'featured_cooperatives': Cooperative.objects.filter(is_public=True)[:4],
        'latest_news': News.objects.filter(is_published=True)[:3],
        'latest_tips': FarmingTip.objects.filter(is_published=True)[:3],
        'key_figures': {
            'cooperatives': Cooperative.objects.filter(is_public=True).count(),
            'members': Member.objects.filter(is_active=True).count(),
            'products': Product.objects.filter(is_published=True).count(),
            'sold': paid_items.aggregate(total=Sum('quantity'))['total'] or 0,
        },
    }
    return render(request, 'public_site/home.html', context)


def product_list(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    region = request.GET.get('region', '').strip()
    products = Product.objects.filter(
        is_published=True,
        quantity_available__gt=0,
    ).select_related('cooperative', 'category')
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(cooperative__name__icontains=query)
        )
    if category:
        products = products.filter(category_id=category)
    if region:
        products = products.filter(cooperative__region=region)
    return render(request, 'public_site/product_list.html', {
        'products': products,
        'categories': ProductCategory.objects.filter(is_active=True),
        'regions': Cooperative.objects.filter(is_public=True).values_list(
            'region', flat=True
        ).distinct().order_by('region'),
        'query': query,
        'selected_category': category,
        'selected_region': region,
    })


def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.select_related('cooperative', 'category'),
        pk=pk,
        is_published=True,
    )
    return render(request, 'public_site/product_detail.html', {'product': product})


def cooperative_list(request):
    region = request.GET.get('region', '').strip()
    cooperatives = Cooperative.objects.filter(is_public=True)
    if region:
        cooperatives = cooperatives.filter(region=region)
    return render(request, 'public_site/cooperative_list.html', {
        'cooperatives': cooperatives,
        'regions': Cooperative.objects.filter(is_public=True).values_list(
            'region', flat=True
        ).distinct().order_by('region'),
        'selected_region': region,
    })


def cooperative_detail(request, pk):
    cooperative = get_object_or_404(Cooperative, pk=pk, is_public=True)
    products = cooperative.products.filter(
        is_published=True,
        quantity_available__gt=0,
    ).select_related('category')[:8]
    return render(request, 'public_site/cooperative_detail.html', {
        'cooperative': cooperative,
        'products': products,
    })


def training_list(request):
    theme = request.GET.get('theme', '').strip()
    courses = Course.objects.filter(is_published=True).select_related('author')
    if theme:
        courses = courses.filter(theme=theme)
    return render(request, 'public_site/training_list.html', {
        'courses': courses,
        'themes': Course.Theme.choices,
        'selected_theme': theme,
        'tips': FarmingTip.objects.filter(is_published=True)[:6],
    })


def training_detail(request, pk):
    course = get_object_or_404(
        Course.objects.prefetch_related('questions__choices'),
        pk=pk,
        is_published=True,
    )
    latest_attempt = None
    course_progress = None
    quiz_progress = None
    video_required = course.has_video
    video_completed = not video_required
    if request.user.is_authenticated:
        latest_attempt = request.user.quiz_attempts.filter(course=course).first()
        course_progress, _ = CourseProgress.objects.get_or_create(
            user=request.user,
            course=course,
        )
        video_completed = not video_required or course_progress.video_completed
        quiz_progress, _ = QuizProgress.objects.get_or_create(
            user=request.user,
            course=course,
        )
        if latest_attempt and quiz_progress.status != QuizProgress.Status.COMPLETED:
            quiz_progress.status = QuizProgress.Status.COMPLETED
            quiz_progress.score = latest_attempt.score
            quiz_progress.total = latest_attempt.total
            quiz_progress.completed_at = latest_attempt.completed_at
            quiz_progress.save(update_fields=[
                'status',
                'score',
                'total',
                'completed_at',
                'updated_at',
            ])
    quiz_state = {
        'answers': getattr(quiz_progress, 'answers', {}) or {},
        'current_index': getattr(quiz_progress, 'current_index', 0) or 0,
    }
    return render(request, 'public_site/training_detail.html', {
        'course': course,
        'latest_attempt': latest_attempt,
        'course_progress': course_progress,
        'quiz_progress': quiz_progress,
        'quiz_state': quiz_state,
        'video_required': video_required,
        'video_completed': video_completed,
        'quiz_completed': bool(latest_attempt),
    })


@login_required
def training_quiz_submit(request, pk):
    course = get_object_or_404(
        Course.objects.prefetch_related('questions__choices'),
        pk=pk,
        is_published=True,
    )
    if request.method != 'POST':
        return redirect('public_site:training_detail', pk=course.pk)

    questions = list(course.questions.all())
    if not questions:
        messages.info(request, 'Aucun quiz disponible pour cette formation.')
        return redirect('public_site:training_detail', pk=course.pk)

    if request.user.quiz_attempts.filter(course=course).exists():
        messages.info(request, 'Vous avez deja termine ce quiz.')
        return redirect('public_site:training_detail', pk=course.pk)

    course_progress, _ = CourseProgress.objects.get_or_create(
        user=request.user,
        course=course,
    )
    if course.has_video and not course_progress.video_completed:
        messages.error(request, 'Regardez la video jusqu’a la fin avant de commencer le quiz.')
        return redirect('public_site:training_detail', pk=course.pk)

    score = 0
    answers = {}
    for question in questions:
        selected_id = request.POST.get(f'question_{question.pk}')
        if selected_id:
            answers[str(question.pk)] = str(selected_id)
        if selected_id and question.choices.filter(pk=selected_id, is_correct=True).exists():
            score += 1

    attempt = QuizAttempt.objects.create(
        user=request.user,
        course=course,
        score=score,
        total=len(questions),
    )
    quiz_progress, _ = QuizProgress.objects.get_or_create(
        user=request.user,
        course=course,
    )
    quiz_progress.answers = answers
    quiz_progress.current_index = max(len(questions) - 1, 0)
    quiz_progress.status = QuizProgress.Status.COMPLETED
    quiz_progress.score = attempt.score
    quiz_progress.total = attempt.total
    quiz_progress.completed_at = attempt.completed_at
    quiz_progress.save(update_fields=[
        'answers',
        'current_index',
        'status',
        'score',
        'total',
        'completed_at',
        'updated_at',
    ])
    messages.success(
        request,
        f'Quiz termine : {attempt.score}/{attempt.total} ({attempt.percentage} %).',
    )
    return redirect('public_site:training_detail', pk=course.pk)


@login_required
@require_POST
def training_video_complete(request, pk):
    course = get_object_or_404(Course, pk=pk, is_published=True)
    progress, _ = CourseProgress.objects.get_or_create(
        user=request.user,
        course=course,
    )
    progress.video_completed = True
    progress.save(update_fields=['video_completed', 'updated_at'])
    return JsonResponse({'ok': True, 'video_completed': True})


@login_required
@require_POST
def training_quiz_progress(request, pk):
    course = get_object_or_404(Course, pk=pk, is_published=True)
    if request.user.quiz_attempts.filter(course=course).exists():
        return JsonResponse({
            'ok': False,
            'completed': True,
            'message': 'Quiz deja termine.',
        }, status=409)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'message': 'Donnees invalides.'}, status=400)

    progress, _ = QuizProgress.objects.get_or_create(
        user=request.user,
        course=course,
    )
    progress.answers = {
        str(key): str(value)
        for key, value in payload.get('answers', {}).items()
        if value
    }
    progress.current_index = max(int(payload.get('current_index') or 0), 0)
    progress.status = QuizProgress.Status.IN_PROGRESS
    progress.completed_at = None
    progress.save(update_fields=[
        'answers',
        'current_index',
        'status',
        'completed_at',
        'updated_at',
    ])
    return JsonResponse({
        'ok': True,
        'answers': progress.answers,
        'current_index': progress.current_index,
    })


def news_list(request):
    return render(request, 'public_site/news_list.html', {
        'news_items': News.objects.filter(is_published=True),
    })


def news_detail(request, pk):
    item = get_object_or_404(News, pk=pk, is_published=True)
    return render(request, 'public_site/news_detail.html', {'item': item})


@user_passes_test(is_admin, login_url='accounts:login')
def news_manage_list(request):
    query = request.GET.get('q', '').strip()
    news_items = News.objects.all()
    if query:
        news_items = news_items.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(content__icontains=query)
        )
    return render(request, 'public_site/news_manage_list.html', {
        'news_items': news_items,
        'query': query,
        'published_count': News.objects.filter(is_published=True).count(),
        'draft_count': News.objects.filter(is_published=False).count(),
    })


@user_passes_test(is_admin, login_url='accounts:login')
def news_create(request):
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save()
            messages.success(request, 'Actualite creee avec succes.')
            return redirect('public_site:news_manage_update', pk=news.pk)
    else:
        form = NewsForm()
    return render(request, 'public_site/news_manage_form.html', {
        'form': form,
        'title': 'Ajouter une actualite',
        'submit_label': 'Enregistrer',
    })


@user_passes_test(is_admin, login_url='accounts:login')
def news_update(request, pk):
    news = get_object_or_404(News, pk=pk)
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news)
        if form.is_valid():
            form.save()
            messages.success(request, 'Actualite mise a jour.')
            return redirect('public_site:news_manage_update', pk=news.pk)
    else:
        form = NewsForm(instance=news)
    return render(request, 'public_site/news_manage_form.html', {
        'form': form,
        'title': 'Modifier l actualite',
        'submit_label': 'Mettre a jour',
        'news': news,
    })


@user_passes_test(is_admin, login_url='accounts:login')
def news_delete(request, pk):
    news = get_object_or_404(News, pk=pk)
    if request.method == 'POST':
        news.delete()
        messages.success(request, 'Actualite supprimee.')
        return redirect('public_site:news_manage_list')
    return render(request, 'public_site/news_manage_confirm_delete.html', {
        'news': news,
    })


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST, user=request.user)
        if form.is_valid():
            contact_message = form.save(commit=False)
            if request.user.is_authenticated:
                contact_message.sender = request.user
            contact_message.save()
            messages.success(
                request,
                'Votre message a bien ete envoye. Vous pouvez suivre son traitement dans votre espace.',
            )
            return redirect('public_site:contact')
    else:
        form = ContactForm(user=request.user)
    return render(request, 'public_site/contact.html', {
        'form': form,
        'platform': _platform_info(),
    })
