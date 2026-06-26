from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView

from cooperatives.models import Cooperative
from members.models import Member
from payments.models import Payment
from productions.models import Production
from products.models import Product
from sales.models import Order, OrderItem
from training.models import Course
from public_site.forms import ContactReplyForm
from public_site.models import ContactMessage

from .access import is_admin, user_cooperative, user_member, user_role
from .forms import ProfileForm, RoleUpdateForm, SignUpForm
from .models import UserProfile


MONTH_NAMES = (
    'Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Juin',
    'Juil', 'Aout', 'Sep', 'Oct', 'Nov', 'Dec',
)


def _month_start(value):
    return date(value.year, value.month, 1)


def _shift_month(value, offset):
    month_index = value.year * 12 + value.month - 1 + offset
    return date(month_index // 12, month_index % 12 + 1, 1)


def _monthly_series(rows, month_key='month', value_key='total', months=6):
    current_month = _month_start(timezone.localdate())
    first_month = _shift_month(current_month, -(months - 1))
    values = {
        _month_start(row[month_key]): row[value_key] or 0
        for row in rows
        if row[month_key]
    }
    maximum = max((float(value) for value in values.values()), default=0)
    series = []
    for offset in range(months):
        month = _shift_month(first_month, offset)
        value = values.get(month, 0)
        series.append({
            'label': f'{MONTH_NAMES[month.month - 1]} {str(month.year)[-2:]}',
            'value': value,
            'percentage': round(float(value) / maximum * 100, 1) if maximum else 0,
        })
    return series


def _ranked_rows(rows, label_key, value_key='total', limit=6):
    rows = list(rows[:limit])
    maximum = max((float(row[value_key] or 0) for row in rows), default=0)
    for row in rows:
        row['label'] = row[label_key] or 'Non renseigne'
        row['value'] = row[value_key] or 0
        row['percentage'] = (
            round(float(row['value']) / maximum * 100, 1)
            if maximum else 0
        )
    return rows


def _growth(current, previous):
    current = float(current or 0)
    previous = float(previous or 0)
    if previous == 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100, 1)


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        messages.success(self.request, 'Compte cree avec succes. Vous pouvez vous connecter.')
        return super().form_valid(form)


class RoleAwareLoginView(LoginView):
    def get_success_url(self):
        destination = self.get_redirect_url()
        role = user_role(self.request.user)
        buyer_only_paths = ('/ventes/panier/', '/ventes/commande/valider/')
        if (
            destination
            and destination.startswith(buyer_only_paths)
            and role != UserProfile.Role.BUYER
        ):
            destination = ''
        if destination:
            return destination
        if role == UserProfile.Role.BUYER:
            return reverse('public_site:home')
        return reverse('accounts:dashboard')


@login_required
def dashboard(request):
    profile = getattr(request.user, 'profile', None)
    role = user_role(request.user)
    if role == UserProfile.Role.BUYER:
        return redirect('public_site:home')
    context = {
        'profile': profile,
        'role': role,
        'is_admin': role == UserProfile.Role.ADMIN,
        'is_manager': role == UserProfile.Role.COOPERATIVE_MANAGER,
        'is_farmer': role == UserProfile.Role.FARMER,
        'is_buyer': role == UserProfile.Role.BUYER,
        'role_display': dict(UserProfile.Role.choices).get(role, 'Utilisateur'),
    }

    if context['is_admin']:
        successful_payments = Payment.objects.filter(status=Payment.Status.SUCCESS)
        paid_items = OrderItem.objects.filter(
            order__payment__status=Payment.Status.SUCCESS
        )
        today = timezone.localdate()
        current_month = _month_start(today)
        previous_month = _shift_month(current_month, -1)
        next_month = _shift_month(current_month, 1)

        current_revenue = successful_payments.filter(
            paid_at__date__gte=current_month,
            paid_at__date__lt=next_month,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        previous_revenue = successful_payments.filter(
            paid_at__date__gte=previous_month,
            paid_at__date__lt=current_month,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        current_production = Production.objects.filter(
            harvest_date__gte=current_month,
            harvest_date__lt=next_month,
        ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')
        previous_production = Production.objects.filter(
            harvest_date__gte=previous_month,
            harvest_date__lt=current_month,
        ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')

        monthly_revenue = _monthly_series(
            successful_payments.annotate(
                month=TruncMonth('paid_at')
            ).values('month').annotate(
                total=Sum('amount')
            ).order_by('month')
        )
        monthly_orders = _monthly_series(
            Order.objects.annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                total=Count('id')
            ).order_by('month')
        )
        production_by_product = _ranked_rows(
            Production.objects.values('product__name').annotate(
                total=Sum('quantity')
            ).order_by('-total'),
            'product__name',
        )
        sales_by_product = _ranked_rows(
            paid_items.values('product_name').annotate(
                total=Sum('quantity')
            ).order_by('-total'),
            'product_name',
        )

        total_orders = Order.objects.count()
        status_colors = {
            Order.Status.PENDING_PAYMENT: '#f59e0b',
            Order.Status.PAID: '#10b981',
            Order.Status.PROCESSING: '#3b82f6',
            Order.Status.DELIVERED: '#06b6d4',
            Order.Status.CANCELLED: '#ef4444',
        }
        status_counts = dict(
            Order.objects.values_list('status').annotate(total=Count('id'))
        )
        order_statuses = []
        gradient_parts = []
        gradient_cursor = 0
        for status, label in Order.Status.choices:
            count = status_counts.get(status, 0)
            percentage = round(count / total_orders * 100, 1) if total_orders else 0
            color = status_colors[status]
            order_statuses.append({
                'label': label,
                'count': count,
                'percentage': percentage,
                'color': color,
            })
            if count:
                next_cursor = gradient_cursor + percentage
                gradient_parts.append(
                    f'{color} {gradient_cursor}% {next_cursor}%'
                )
                gradient_cursor = next_cursor
        order_status_gradient = (
            f"conic-gradient({', '.join(gradient_parts)})"
            if gradient_parts else '#e2e8f0'
        )

        role_counts = dict(
            UserProfile.objects.values_list('role').annotate(total=Count('id'))
        )
        total_profiles = sum(role_counts.values())
        role_colors = {
            UserProfile.Role.ADMIN: '#4f46e5',
            UserProfile.Role.COOPERATIVE_MANAGER: '#0891b2',
            UserProfile.Role.FARMER: '#16a34a',
            UserProfile.Role.BUYER: '#f97316',
        }
        role_distribution = [
            {
                'label': label,
                'count': role_counts.get(value, 0),
                'percentage': round(
                    role_counts.get(value, 0) / total_profiles * 100, 1
                ) if total_profiles else 0,
                'color': role_colors[value],
            }
            for value, label in UserProfile.Role.choices
        ]

        top_cooperatives = _ranked_rows(
            paid_items.values('product__cooperative__name').annotate(
                total=Sum('subtotal')
            ).order_by('-total'),
            'product__cooperative__name',
            limit=5,
        )
        context.update({
            'cooperative_count': Cooperative.objects.count(),
            'member_count': Member.objects.filter(is_active=True).count(),
            'farmer_count': UserProfile.objects.filter(
                role=UserProfile.Role.FARMER
            ).count(),
            'buyer_count': UserProfile.objects.filter(
                role=UserProfile.Role.BUYER
            ).count(),
            'order_count': total_orders,
            'global_revenue': successful_payments.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'global_production': Production.objects.aggregate(
                total=Sum('quantity')
            )['total'] or 0,
            'products_sold': paid_items.aggregate(
                total=Sum('quantity')
            )['total'] or 0,
            'new_message_count': ContactMessage.objects.filter(
                status=ContactMessage.Status.NEW
            ).count(),
            'low_stock_count': Product.objects.filter(
                quantity_available__lte=10
            ).count(),
            'published_course_count': Course.objects.filter(
                is_published=True
            ).count(),
            'current_revenue': current_revenue,
            'revenue_growth': _growth(current_revenue, previous_revenue),
            'current_production': current_production,
            'production_growth': _growth(
                current_production, previous_production
            ),
            'monthly_revenue': monthly_revenue,
            'monthly_orders': monthly_orders,
            'production_by_product': production_by_product,
            'sales_by_product': sales_by_product,
            'order_statuses': order_statuses,
            'order_status_gradient': order_status_gradient,
            'role_distribution': role_distribution,
            'top_cooperatives': top_cooperatives,
            'recent_orders': Order.objects.select_related(
                'customer'
            ).prefetch_related('items')[:6],
            'recent_messages': ContactMessage.objects.select_related(
                'sender'
            )[:5],
            'low_stock_products': Product.objects.select_related(
                'cooperative'
            ).filter(quantity_available__lte=10).order_by(
                'quantity_available'
            )[:5],
        })
    elif context['is_manager']:
        cooperative = user_cooperative(request.user)
        context['cooperative'] = cooperative
        if cooperative:
            cooperative_items = OrderItem.objects.filter(
                product__cooperative=cooperative
            )
            cooperative_orders = Order.objects.filter(
                items__product__cooperative=cooperative
            ).distinct()
            paid_cooperative_items = cooperative_items.filter(
                order__payment__status=Payment.Status.SUCCESS
            )
            context.update({
                'member_count': Member.objects.filter(cooperative=cooperative).count(),
                'production_total': Production.objects.filter(
                    member__cooperative=cooperative
                ).aggregate(total=Sum('quantity'))['total'] or 0,
                'product_count': Product.objects.filter(
                    cooperative=cooperative
                ).count(),
                'order_count': cooperative_orders.count(),
                'cooperative_revenue': paid_cooperative_items.aggregate(
                    total=Sum('subtotal')
                )['total'] or 0,
                'cooperative_products_sold': paid_cooperative_items.aggregate(
                    total=Sum('quantity')
                )['total'] or 0,
                'manager_monthly_revenue': _monthly_series(
                    paid_cooperative_items.annotate(
                        month=TruncMonth('order__payment__paid_at')
                    ).values('month').annotate(
                        total=Sum('subtotal')
                    ).order_by('month')
                ),
                'manager_top_products': _ranked_rows(
                    paid_cooperative_items.values('product_name').annotate(
                        total=Sum('quantity')
                    ).order_by('-total'),
                    'product_name',
                ),
                'manager_recent_orders': cooperative_orders.select_related(
                    'customer'
                )[:5],
            })
        else:
            context.update({
                'member_count': 0,
                'production_total': 0,
                'product_count': 0,
                'order_count': 0,
            })
    elif context['is_farmer']:
        member = user_member(request.user)
        productions = Production.objects.filter(member=member) if member else Production.objects.none()
        context.update({
            'member': member,
            'production_count': productions.count(),
            'production_total': productions.aggregate(
                total=Sum('quantity')
            )['total'] or 0,
            'farmer_revenue': productions.aggregate(
                total=Sum('estimated_price')
            )['total'] or 0,
            'course_count': Course.objects.filter(is_published=True).count(),
            'farmer_monthly_production': _monthly_series(
                productions.annotate(
                    month=TruncMonth('harvest_date')
                ).values('month').annotate(
                    total=Sum('quantity')
                ).order_by('month')
            ),
            'farmer_products': _ranked_rows(
                productions.values('product__name').annotate(
                    total=Sum('quantity')
                ).order_by('-total'),
                'product__name',
                limit=5,
            ),
            'recent_productions': productions.select_related('product')[:5],
        })
    else:
        orders = request.user.orders.all()
        context.update({
            'order_count': orders.count(),
            'pending_order_count': orders.filter(
                status=Order.Status.PENDING_PAYMENT
            ).count(),
            'payment_count': orders.filter(payment__isnull=False).count(),
        })
    return render(request, 'accounts/dashboard.html', context)


def is_platform_admin(user):
    return is_admin(user)


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


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a ete mis a jour.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(user=request.user)
    return render(request, 'accounts/profile.html', {
        'form': form,
        'base_template': (
            'public_site/base.html'
            if user_role(request.user) == UserProfile.Role.BUYER
            else 'accounts/base.html'
        ),
    })


@login_required
def my_messages(request):
    contact_messages = request.user.contact_messages.all()
    return render(request, 'accounts/my_messages.html', {
        'contact_messages': contact_messages,
        'base_template': (
            'public_site/base.html'
            if user_role(request.user) == UserProfile.Role.BUYER
            else 'accounts/base.html'
        ),
    })


@login_required
def my_message_detail(request, pk):
    contact_message = get_object_or_404(
        request.user.contact_messages.all(),
        pk=pk,
    )
    return render(request, 'accounts/my_message_detail.html', {
        'contact_message': contact_message,
        'base_template': (
            'public_site/base.html'
            if user_role(request.user) == UserProfile.Role.BUYER
            else 'accounts/base.html'
        ),
    })


@user_passes_test(is_platform_admin, login_url='accounts:login')
def message_inbox(request):
    selected_status = request.GET.get('status', '').strip()
    contact_messages = ContactMessage.objects.select_related(
        'sender', 'processed_by'
    )
    if selected_status:
        contact_messages = contact_messages.filter(status=selected_status)
    return render(request, 'accounts/message_inbox.html', {
        'contact_messages': contact_messages,
        'statuses': ContactMessage.Status.choices,
        'selected_status': selected_status,
        'new_message_count': ContactMessage.objects.filter(
            status=ContactMessage.Status.NEW
        ).count(),
    })


@user_passes_test(is_platform_admin, login_url='accounts:login')
def message_manage(request, pk):
    contact_message = get_object_or_404(
        ContactMessage.objects.select_related('sender', 'processed_by'),
        pk=pk,
    )
    if request.method == 'POST':
        form = ContactReplyForm(request.POST, instance=contact_message)
        if form.is_valid():
            contact_message = form.save(commit=False)
            if contact_message.admin_reply:
                if contact_message.status != ContactMessage.Status.CLOSED:
                    contact_message.status = ContactMessage.Status.ANSWERED
                contact_message.replied_at = timezone.now()
            contact_message.processed_by = request.user
            contact_message.save()
            messages.success(request, 'Le message a ete mis a jour.')
            return redirect('accounts:message_manage', pk=contact_message.pk)
    else:
        form = ContactReplyForm(instance=contact_message)
    return render(request, 'accounts/message_manage.html', {
        'contact_message': contact_message,
        'form': form,
    })
