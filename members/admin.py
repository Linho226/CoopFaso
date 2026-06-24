from django.contrib import admin

from .models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'gender', 'cooperative', 'phone', 'is_active')
    list_filter = ('gender', 'is_active', 'cooperative')
    search_fields = ('first_name', 'last_name', 'phone', 'address', 'cooperative__name')
    autocomplete_fields = ('cooperative',)
    ordering = ('last_name', 'first_name')
