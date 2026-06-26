from django.contrib import admin

from .models import Course, QuizAttempt, QuizChoice, QuizQuestion


class QuizChoiceInline(admin.TabularInline):
    model = QuizChoice
    extra = 3


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'course', 'order')
    list_filter = ('course',)
    inlines = (QuizChoiceInline,)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'theme', 'author', 'is_published', 'updated_at')
    list_filter = ('theme', 'is_published')
    search_fields = ('title', 'summary', 'content')


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'score', 'total', 'completed_at')
    list_filter = ('course', 'completed_at')
    readonly_fields = ('user', 'course', 'score', 'total', 'completed_at')
