from django.urls import path

from . import views

app_name = 'payments'

urlpatterns = [
    path('commande/<int:order_id>/', views.pay_order, name='pay'),
    path('historique/', views.payment_history, name='history'),
    path('recu/<int:pk>/', views.receipt, name='receipt'),
]
