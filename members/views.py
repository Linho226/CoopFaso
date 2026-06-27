from django.contrib import messages
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.access import is_manager, roles_required, user_cooperative
from accounts.models import UserProfile
from cooperatives.models import Cooperative

from .forms import MemberForm
from .models import Member


def _selected_cooperative(request):
    if is_manager(request.user):
        return user_cooperative(request.user)
    cooperative_id = request.GET.get('cooperative') or request.POST.get('cooperative')
    if cooperative_id:
        return Cooperative.objects.filter(pk=cooperative_id).first()
    return None


@roles_required(UserProfile.Role.ADMIN, UserProfile.Role.COOPERATIVE_MANAGER)
def member_list(request):
    query = request.GET.get('q', '').strip()
    selected_cooperative = request.GET.get('cooperative', '').strip()
    members = Member.objects.select_related('cooperative')
    if is_manager(request.user):
        manager_cooperative = user_cooperative(request.user)
        members = members.filter(cooperative=manager_cooperative)
        selected_cooperative = str(getattr(manager_cooperative, 'pk', ''))
    elif selected_cooperative:
        members = members.filter(cooperative_id=selected_cooperative)
    if query:
        members = members.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(phone__icontains=query)
            | Q(address__icontains=query)
            | Q(cooperative__name__icontains=query)
        )
    cooperatives = Cooperative.objects.all()
    if selected_cooperative:
        cooperatives = cooperatives.filter(pk=selected_cooperative)
    grouped_cooperatives = cooperatives.prefetch_related(
        Prefetch('members', queryset=members, to_attr='filtered_members')
    )
    return render(request, 'members/member_list.html', {
        'members': members,
        'grouped_cooperatives': grouped_cooperatives,
        'cooperatives': Cooperative.objects.all(),
        'query': query,
        'selected_cooperative': selected_cooperative,
        'is_manager_view': is_manager(request.user),
        'can_manage': True,
    })


@roles_required(UserProfile.Role.ADMIN, UserProfile.Role.COOPERATIVE_MANAGER)
def member_detail(request, pk):
    members = Member.objects.select_related('cooperative')
    if is_manager(request.user):
        members = members.filter(cooperative=user_cooperative(request.user))
    member = get_object_or_404(members, pk=pk)
    return render(request, 'members/member_detail.html', {
        'member': member,
        'can_manage': True,
    })


@roles_required(UserProfile.Role.ADMIN, UserProfile.Role.COOPERATIVE_MANAGER)
def member_create(request):
    cooperative = _selected_cooperative(request)
    if request.method == 'POST':
        form = MemberForm(request.POST, request.FILES, cooperative=cooperative)
        if form.is_valid():
            member = form.save()
            messages.success(request, 'Membre ajoute avec succes.')
            return redirect(member)
    else:
        form = MemberForm(cooperative=cooperative)
    return render(request, 'members/member_form.html', {
        'form': form,
        'title': 'Ajouter un membre',
        'submit_label': 'Ajouter',
    })


@roles_required(UserProfile.Role.ADMIN, UserProfile.Role.COOPERATIVE_MANAGER)
def member_update(request, pk):
    members = Member.objects.all()
    if is_manager(request.user):
        members = members.filter(cooperative=user_cooperative(request.user))
    member = get_object_or_404(members, pk=pk)
    cooperative = user_cooperative(request.user) if is_manager(request.user) else None
    if request.method == 'POST':
        form = MemberForm(
            request.POST,
            request.FILES,
            instance=member,
            cooperative=cooperative,
        )
        if form.is_valid():
            member = form.save()
            messages.success(request, 'Membre modifie avec succes.')
            return redirect(member)
    else:
        form = MemberForm(instance=member, cooperative=cooperative)
    return render(request, 'members/member_form.html', {
        'form': form,
        'title': 'Modifier le membre',
        'submit_label': 'Enregistrer',
        'member': member,
    })


@roles_required(UserProfile.Role.ADMIN, UserProfile.Role.COOPERATIVE_MANAGER)
def member_deactivate(request, pk):
    members = Member.objects.all()
    if is_manager(request.user):
        members = members.filter(cooperative=user_cooperative(request.user))
    member = get_object_or_404(members, pk=pk)
    if request.method == 'POST':
        member.is_active = False
        member.save(update_fields=['is_active', 'updated_at'])
        messages.success(request, 'Membre desactive avec succes.')
        return redirect('members:list')
    return render(request, 'members/member_confirm_deactivate.html', {
        'member': member,
    })
