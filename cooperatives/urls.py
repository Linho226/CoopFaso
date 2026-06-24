from django.urls import path

from . import views

app_name = 'cooperatives'

urlpatterns = [
    path('', views.cooperative_list, name='list'),
    path('creer/', views.cooperative_create, name='create'),
    path('<int:pk>/', views.cooperative_detail, name='detail'),
    path('<int:pk>/modifier/', views.cooperative_update, name='update'),
    path('<int:pk>/supprimer/', views.cooperative_delete, name='delete'),
]
