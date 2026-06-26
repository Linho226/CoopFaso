from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import StyledAuthenticationForm, StyledPasswordResetForm, StyledSetPasswordForm

app_name = 'accounts'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('inscription/', views.SignUpView.as_view(), name='register'),
    path(
        'connexion/',
        views.RoleAwareLoginView.as_view(
            template_name='accounts/login.html',
            authentication_form=StyledAuthenticationForm,
        ),
        name='login',
    ),
    path('deconnexion/', auth_views.LogoutView.as_view(), name='logout'),
    path(
        'mot-de-passe/reinitialiser/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset_form.html',
            email_template_name='accounts/password_reset_email.html',
            form_class=StyledPasswordResetForm,
            success_url=reverse_lazy('accounts:password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'mot-de-passe/reinitialiser/envoye/',
        auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
        name='password_reset_done',
    ),
    path(
        'mot-de-passe/reinitialiser/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            form_class=StyledSetPasswordForm,
            success_url=reverse_lazy('accounts:password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'mot-de-passe/reinitialiser/termine/',
        auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
        name='password_reset_complete',
    ),
    path('utilisateurs/roles/', views.user_roles, name='user_roles'),
    path('utilisateurs/<int:user_id>/role/', views.update_user_role, name='update_user_role'),
    path('profil/', views.profile, name='profile'),
    path('messages/', views.my_messages, name='my_messages'),
    path('messages/<int:pk>/', views.my_message_detail, name='my_message_detail'),
    path('administration/messages/', views.message_inbox, name='message_inbox'),
    path(
        'administration/messages/<int:pk>/',
        views.message_manage,
        name='message_manage',
    ),
]
