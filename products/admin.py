from django.contrib import admin

from .models import Product, ProductCategory


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'cooperative', 'price', 'quantity_available', 'is_published')
    list_filter = ('category', 'cooperative', 'is_published', 'created_at')
    search_fields = ('name', 'description', 'cooperative__name')
    autocomplete_fields = ('cooperative',)
