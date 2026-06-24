from django.urls import path

from . import views

app_name = 'members'

urlpatterns = [
    path('', views.member_list, name='list'),
    path('ajouter/', views.member_create, name='create'),
    path('<int:pk>/', views.member_detail, name='detail'),
    path('<int:pk>/modifier/', views.member_update, name='update'),
    path('<int:pk>/desactiver/', views.member_deactivate, name='deactivate'),
]
