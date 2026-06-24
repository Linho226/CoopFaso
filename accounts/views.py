from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import RoleUpdateForm, SignUpForm


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        messages.success(self.request, 'Compte cree avec succes. Vous pouvez vous connecter.')
        return super().form_valid(form)


@login_required
def dashboard(request):
    profile = getattr(request.user, 'profile', None)
    return render(request, 'accounts/dashboard.html', {'profile': profile})


def is_platform_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return getattr(getattr(user, 'profile', None), 'role', None) == 'ADMIN'


@user_passes_test(is_platform_admin, login_url='accounts:login')
def user_roles(request):
    users = User.objects.select_related('profile').order_by('username')
    return render(request, 'accounts/user_roles.html', {'users': users})


@user_passes_test(is_platform_admin, login_url='accounts:login')
def update_user_role(request, user_id):
    user = get_object_or_404(User.objects.select_related('profile'), pk=user_id)
    profile = user.profile
    if request.method == 'POST':
        form = RoleUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Role mis a jour avec succes.')
            return redirect('accounts:user_roles')
    else:
        form = RoleUpdateForm(instance=profile)
    return render(request, 'accounts/update_user_role.html', {'form': form, 'managed_user': user})
