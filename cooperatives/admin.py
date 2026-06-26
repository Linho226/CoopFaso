from django.contrib import admin

from .models import Cooperative


@admin.register(Cooperative)
class CooperativeAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'province', 'phone', 'is_public', 'creation_date')
    list_filter = ('region', 'province', 'is_public', 'creation_date')
    search_fields = ('name', 'address', 'phone', 'email', 'region', 'province')
    ordering = ('name',)
