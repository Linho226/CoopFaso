from django.urls import path

from . import views

app_name = 'public_site'

urlpatterns = [
    path('', views.home, name='home'),
    path('catalogue/', views.product_list, name='products'),
    path('catalogue/<int:pk>/', views.product_detail, name='product_detail'),
    path('cooperatives/', views.cooperative_list, name='cooperatives'),
    path('cooperatives/<int:pk>/', views.cooperative_detail, name='cooperative_detail'),
    path('formations/', views.training_list, name='trainings'),
    path('formations/<int:pk>/', views.training_detail, name='training_detail'),
    path('formations/<int:pk>/quiz/', views.training_quiz_submit, name='training_quiz_submit'),
    path('formations/<int:pk>/quiz/progression/', views.training_quiz_progress, name='training_quiz_progress'),
    path('formations/<int:pk>/video/terminee/', views.training_video_complete, name='training_video_complete'),
    path('actualites/', views.news_list, name='news'),
    path('actualites/<int:pk>/', views.news_detail, name='news_detail'),
    path('gestion/actualites/', views.news_manage_list, name='news_manage_list'),
    path('gestion/actualites/ajouter/', views.news_create, name='news_manage_create'),
    path(
        'gestion/actualites/<int:pk>/modifier/',
        views.news_update,
        name='news_manage_update',
    ),
    path(
        'gestion/actualites/<int:pk>/supprimer/',
        views.news_delete,
        name='news_manage_delete',
    ),
    path('contact/', views.contact, name='contact'),
]
