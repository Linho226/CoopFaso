from django.contrib import admin

from .models import ContactMessage, FarmingTip, News, PlatformInfo


@admin.register(PlatformInfo)
class PlatformInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'updated_at')

    def has_add_permission(self, request):
        return not PlatformInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_at', 'is_published')
    list_filter = ('is_published', 'published_at')
    search_fields = ('title', 'summary', 'content')
    date_hierarchy = 'published_at'


@admin.register(FarmingTip)
class FarmingTipAdmin(admin.ModelAdmin):
    list_display = ('title', 'theme', 'is_published', 'created_at')
    list_filter = ('theme', 'is_published')
    search_fields = ('title', 'content', 'theme')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'subject', 'email', 'status', 'created_at')
    list_filter = ('category', 'status', 'created_at')
    search_fields = ('name', 'email', 'phone', 'subject', 'message')
    readonly_fields = (
        'sender', 'name', 'email', 'phone', 'category',
        'subject', 'message', 'created_at',
    )
