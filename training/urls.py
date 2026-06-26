from django.urls import path

from . import views

app_name = 'training'

urlpatterns = [
    path('', views.course_list, name='list'),
    path('publier/', views.course_create, name='create'),
    path('<int:pk>/', views.course_detail, name='detail'),
    path('<int:pk>/modifier/', views.course_update, name='update'),
    path('<int:pk>/quiz/', views.quiz_submit, name='quiz_submit'),
]
