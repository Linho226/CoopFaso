from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import UserProfile


def user_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser or user.is_staff:
        return UserProfile.Role.ADMIN
    return getattr(getattr(user, 'profile', None), 'role', None)


def is_admin(user):
    return user_role(user) == UserProfile.Role.ADMIN


def is_manager(user):
    return user_role(user) == UserProfile.Role.COOPERATIVE_MANAGER


def is_farmer(user):
    return user_role(user) == UserProfile.Role.FARMER


def is_buyer(user):
    return user_role(user) == UserProfile.Role.BUYER


def user_cooperative(user):
    return getattr(getattr(user, 'profile', None), 'cooperative', None)


def user_member(user):
    from members.models import Member

    profile = getattr(user, 'profile', None)
    queryset = Member.objects.select_related('cooperative')
    if profile and profile.cooperative_id:
        queryset = queryset.filter(cooperative_id=profile.cooperative_id)
    if profile and profile.phone:
        member = queryset.filter(phone=profile.phone).first()
        if member:
            return member
    if user.first_name and user.last_name:
        return queryset.filter(
            first_name__iexact=user.first_name,
            last_name__iexact=user.last_name,
        ).first()
    return None


def roles_required(*allowed_roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if user_role(request.user) not in allowed_roles:
                messages.error(
                    request,
                    "Vous n'avez pas acces a cette fonctionnalite avec votre role.",
                )
                return redirect('accounts:dashboard')
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
