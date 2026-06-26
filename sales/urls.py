from django.urls import path

from . import views

app_name = 'sales'

urlpatterns = [
    path('panier/', views.cart_detail, name='cart'),
    path('panier/ajouter/<int:product_id>/', views.cart_add, name='cart_add'),
    path('panier/modifier/<int:product_id>/', views.cart_update, name='cart_update'),
    path('panier/retirer/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('commande/valider/', views.checkout, name='checkout'),
    path('commandes/', views.order_list, name='order_list'),
    path('commandes/<int:pk>/', views.order_detail, name='order_detail'),
]
