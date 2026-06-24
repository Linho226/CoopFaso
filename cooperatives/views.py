from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CooperativeForm
from .models import Cooperative


def can_manage_cooperatives(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    role = getattr(getattr(user, 'profile', None), 'role', None)
    return role in {'ADMIN', 'COOPERATIVE_MANAGER'}


@login_required
def cooperative_list(request):
    cooperatives = Cooperative.objects.all()
    return render(request, 'cooperatives/cooperative_list.html', {
        'cooperatives': cooperatives,
        'can_manage': can_manage_cooperatives(request.user),
    })


@login_required
def cooperative_detail(request, pk):
    cooperative = get_object_or_404(Cooperative, pk=pk)
    return render(request, 'cooperatives/cooperative_detail.html', {
        'cooperative': cooperative,
        'can_manage': can_manage_cooperatives(request.user),
    })


@user_passes_test(can_manage_cooperatives, login_url='accounts:login')
def cooperative_create(request):
    if request.method == 'POST':
        form = CooperativeForm(request.POST)
        if form.is_valid():
            cooperative = form.save()
            messages.success(request, 'Cooperative creee avec succes.')
            return redirect(cooperative)
    else:
        form = CooperativeForm()
    return render(request, 'cooperatives/cooperative_form.html', {
        'form': form,
        'title': 'Creer une cooperative',
        'submit_label': 'Creer',
    })


@user_passes_test(can_manage_cooperatives, login_url='accounts:login')
def cooperative_update(request, pk):
    cooperative = get_object_or_404(Cooperative, pk=pk)
    if request.method == 'POST':
        form = CooperativeForm(request.POST, instance=cooperative)
        if form.is_valid():
            cooperative = form.save()
            messages.success(request, 'Cooperative modifiee avec succes.')
            return redirect(cooperative)
    else:
        form = CooperativeForm(instance=cooperative)
    return render(request, 'cooperatives/cooperative_form.html', {
        'form': form,
        'title': 'Modifier la cooperative',
        'submit_label': 'Enregistrer',
        'cooperative': cooperative,
    })


@user_passes_test(can_manage_cooperatives, login_url='accounts:login')
def cooperative_delete(request, pk):
    cooperative = get_object_or_404(Cooperative, pk=pk)
    if request.method == 'POST':
        cooperative.delete()
        messages.success(request, 'Cooperative supprimee avec succes.')
        return redirect('cooperatives:list')
    return render(request, 'cooperatives/cooperative_confirm_delete.html', {
        'cooperative': cooperative,
    })
