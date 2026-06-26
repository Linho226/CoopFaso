from django.contrib import admin

from .models import Production


@admin.register(Production)
class ProductionAdmin(admin.ModelAdmin):
    list_display = ('member', 'product', 'quantity', 'harvest_date', 'estimated_price')
    list_filter = ('harvest_date', 'product', 'member__cooperative')
    search_fields = ('member__first_name', 'member__last_name', 'product__name')
    autocomplete_fields = ('member', 'product')
    date_hierarchy = 'harvest_date'
