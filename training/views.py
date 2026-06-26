from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.access import is_admin, roles_required
from accounts.models import UserProfile

from .forms import CourseForm, QuizQuestionCreateForm
from .models import Course, QuizAttempt, QuizChoice, QuizQuestion


def can_manage_training(user):
    return is_admin(user)


@roles_required(UserProfile.Role.ADMIN, UserProfile.Role.FARMER, UserProfile.Role.BUYER)
def course_list(request):
    query = request.GET.get('q', '').strip()
    theme = request.GET.get('theme', '').strip()
    courses = Course.objects.select_related('author').annotate(
        question_count=Count('questions', distinct=True),
    )
    if not can_manage_training(request.user):
        courses = courses.filter(is_published=True)
    if query:
        courses = courses.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(content__icontains=query)
        )
    if theme:
        courses = courses.filter(theme=theme)
    return render(request, 'training/course_list.html', {
        'courses': courses,
        'query': query,
        'selected_theme': theme,
        'themes': Course.Theme.choices,
        'can_manage': can_manage_training(request.user),
    })


@roles_required(UserProfile.Role.ADMIN, UserProfile.Role.FARMER, UserProfile.Role.BUYER)
def course_detail(request, pk):
    course = get_object_or_404(
        Course.objects.prefetch_related('questions__choices'),
        pk=pk,
    )
    if not course.is_published and not can_manage_training(request.user):
        messages.error(request, 'Ce cours n’est pas encore publie.')
        return redirect('training:list')
    latest_attempt = request.user.quiz_attempts.filter(course=course).first()
    return render(request, 'training/course_detail.html', {
        'course': course,
        'latest_attempt': latest_attempt,
        'can_manage': can_manage_training(request.user),
    })


@roles_required(UserProfile.Role.ADMIN)
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.author = request.user
            course.save()
            messages.success(request, 'Cours publie avec succes.')
            return redirect(course)
    else:
        form = CourseForm()
    return render(request, 'training/course_form.html', {
        'form': form,
        'title': 'Publier un cours',
    })


@roles_required(UserProfile.Role.ADMIN)
def course_update(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cours mis a jour.')
            return redirect(course)
    else:
        form = CourseForm(instance=course)
    return render(request, 'training/course_form.html', {
        'form': form,
        'title': 'Modifier le cours',
        'course': course,
    })


@roles_required(UserProfile.Role.ADMIN)
def course_quiz_manage(request, pk):
    course = get_object_or_404(
        Course.objects.prefetch_related('questions__choices'),
        pk=pk,
    )
    form = QuizQuestionCreateForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete_question':
            question = get_object_or_404(
                course.questions,
                pk=request.POST.get('question_id'),
            )
            question.delete()
            messages.success(request, 'Question supprimee.')
            return redirect('training:quiz_manage', pk=course.pk)

        form = QuizQuestionCreateForm(request.POST)
        if form.is_valid():
            next_order = course.questions.count() + 1
            question = QuizQuestion.objects.create(
                course=course,
                text=form.cleaned_data['question'],
                order=next_order,
            )
            QuizChoice.objects.bulk_create([
                QuizChoice(question=question, **choice)
                for choice in form.choices_payload
            ])
            messages.success(request, 'Question ajoutee au quiz.')
            return redirect('training:quiz_manage', pk=course.pk)

    return render(request, 'training/course_quiz_manage.html', {
        'course': course,
        'form': form,
    })


@roles_required(UserProfile.Role.ADMIN, UserProfile.Role.FARMER, UserProfile.Role.BUYER)
def quiz_submit(request, pk):
    course = get_object_or_404(
        Course.objects.prefetch_related('questions__choices'),
        pk=pk,
        is_published=True,
    )
    if request.method != 'POST':
        return redirect(course)

    questions = list(course.questions.all())
    score = 0
    for question in questions:
        selected_id = request.POST.get(f'question_{question.pk}')
        if selected_id and question.choices.filter(pk=selected_id, is_correct=True).exists():
            score += 1

    attempt = QuizAttempt.objects.create(
        user=request.user,
        course=course,
        score=score,
        total=len(questions),
    )
    messages.success(
        request,
        f'Quiz termine : {attempt.score}/{attempt.total} ({attempt.percentage} %).',
    )
    return redirect(course)
