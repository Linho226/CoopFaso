from django.urls import path
from . import views

app_name = 'productions'

urlpatterns = [
    path('', views.production_list, name='list'),
    path('declarer/', views.production_create, name='create'),
    path('<int:pk>/modifier/', views.production_update, name='update'),
    path('statistiques/', views.production_stats, name='stats'),
]
