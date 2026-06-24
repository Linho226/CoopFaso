from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MemberForm
from .models import Member


def can_manage_members(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    role = getattr(getattr(user, 'profile', None), 'role', None)
    return role in {'ADMIN', 'COOPERATIVE_MANAGER'}


@login_required
def member_list(request):
    query = request.GET.get('q', '').strip()
    members = Member.objects.select_related('cooperative')
    if query:
        members = members.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(phone__icontains=query)
            | Q(address__icontains=query)
            | Q(cooperative__name__icontains=query)
        )
    return render(request, 'members/member_list.html', {
        'members': members,
        'query': query,
        'can_manage': can_manage_members(request.user),
    })


@login_required
def member_detail(request, pk):
    member = get_object_or_404(Member.objects.select_related('cooperative'), pk=pk)
    return render(request, 'members/member_detail.html', {
        'member': member,
        'can_manage': can_manage_members(request.user),
    })


@user_passes_test(can_manage_members, login_url='accounts:login')
def member_create(request):
    if request.method == 'POST':
        form = MemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save()
            messages.success(request, 'Membre ajoute avec succes.')
            return redirect(member)
    else:
        form = MemberForm()
    return render(request, 'members/member_form.html', {
        'form': form,
        'title': 'Ajouter un membre',
        'submit_label': 'Ajouter',
    })


@user_passes_test(can_manage_members, login_url='accounts:login')
def member_update(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        form = MemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            member = form.save()
            messages.success(request, 'Membre modifie avec succes.')
            return redirect(member)
    else:
        form = MemberForm(instance=member)
    return render(request, 'members/member_form.html', {
        'form': form,
        'title': 'Modifier le membre',
        'submit_label': 'Enregistrer',
        'member': member,
    })


@user_passes_test(can_manage_members, login_url='accounts:login')
def member_deactivate(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        member.is_active = False
        member.save(update_fields=['is_active', 'updated_at'])
        messages.success(request, 'Membre desactive avec succes.')
        return redirect('members:list')
    return render(request, 'members/member_confirm_deactivate.html', {'member': member})
