from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('reference', 'order', 'method', 'status', 'amount', 'paid_at')
    list_filter = ('method', 'status', 'created_at')
    search_fields = ('reference', 'order__reference', 'order__customer__username')
    readonly_fields = (
        'reference', 'order', 'method', 'status', 'amount',
        'payer_phone', 'card_last4', 'paid_at', 'created_at',
    )
