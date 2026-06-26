from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from cooperatives.models import Cooperative
from members.models import Member
from products.models import Product, ProductCategory
from sales.models import OrderItem
from training.models import Course

from accounts.access import is_admin

from .forms import ContactForm, NewsForm
from .models import FarmingTip, News, PlatformInfo


def _platform_info():
    return PlatformInfo.objects.first()


def home(request):
    paid_items = OrderItem.objects.filter(order__payment__status='SUCCESS')
    context = {
        'platform': _platform_info(),
        'featured_products': Product.objects.filter(
            is_published=True,
            quantity_available__gt=0,
        ).select_related('cooperative', 'category')[:6],
        'featured_cooperatives': Cooperative.objects.filter(is_public=True)[:4],
        'latest_news': News.objects.filter(is_published=True)[:3],
        'latest_tips': FarmingTip.objects.filter(is_published=True)[:3],
        'key_figures': {
            'cooperatives': Cooperative.objects.filter(is_public=True).count(),
            'members': Member.objects.filter(is_active=True).count(),
            'products': Product.objects.filter(is_published=True).count(),
            'sold': paid_items.aggregate(total=Sum('quantity'))['total'] or 0,
        },
    }
    return render(request, 'public_site/home.html', context)


def product_list(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    region = request.GET.get('region', '').strip()
    products = Product.objects.filter(
        is_published=True,
        quantity_available__gt=0,
    ).select_related('cooperative', 'category')
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(cooperative__name__icontains=query)
        )
    if category:
        products = products.filter(category_id=category)
    if region:
        products = products.filter(cooperative__region=region)
    return render(request, 'public_site/product_list.html', {
        'products': products,
        'categories': ProductCategory.objects.filter(is_active=True),
        'regions': Cooperative.objects.filter(is_public=True).values_list(
            'region', flat=True
        ).distinct().order_by('region'),
        'query': query,
        'selected_category': category,
        'selected_region': region,
    })


def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.select_related('cooperative', 'category'),
        pk=pk,
        is_published=True,
    )
    return render(request, 'public_site/product_detail.html', {'product': product})


def cooperative_list(request):
    region = request.GET.get('region', '').strip()
    cooperatives = Cooperative.objects.filter(is_public=True)
    if region:
        cooperatives = cooperatives.filter(region=region)
    return render(request, 'public_site/cooperative_list.html', {
        'cooperatives': cooperatives,
        'regions': Cooperative.objects.filter(is_public=True).values_list(
            'region', flat=True
        ).distinct().order_by('region'),
        'selected_region': region,
    })


def cooperative_detail(request, pk):
    cooperative = get_object_or_404(Cooperative, pk=pk, is_public=True)
    products = cooperative.products.filter(
        is_published=True,
        quantity_available__gt=0,
    ).select_related('category')[:8]
    return render(request, 'public_site/cooperative_detail.html', {
        'cooperative': cooperative,
        'products': products,
    })


def training_list(request):
    theme = request.GET.get('theme', '').strip()
    courses = Course.objects.filter(is_published=True).select_related('author')
    if theme:
        courses = courses.filter(theme=theme)
    return render(request, 'public_site/training_list.html', {
        'courses': courses,
        'themes': Course.Theme.choices,
        'selected_theme': theme,
        'tips': FarmingTip.objects.filter(is_published=True)[:6],
    })


def training_detail(request, pk):
    course = get_object_or_404(Course, pk=pk, is_published=True)
    return render(request, 'public_site/training_detail.html', {'course': course})


def news_list(request):
    return render(request, 'public_site/news_list.html', {
        'news_items': News.objects.filter(is_published=True),
    })


def news_detail(request, pk):
    item = get_object_or_404(News, pk=pk, is_published=True)
    return render(request, 'public_site/news_detail.html', {'item': item})


@user_passes_test(is_admin, login_url='accounts:login')
def news_manage_list(request):
    query = request.GET.get('q', '').strip()
    news_items = News.objects.all()
    if query:
        news_items = news_items.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(content__icontains=query)
        )
    return render(request, 'public_site/news_manage_list.html', {
        'news_items': news_items,
        'query': query,
        'published_count': News.objects.filter(is_published=True).count(),
        'draft_count': News.objects.filter(is_published=False).count(),
    })


@user_passes_test(is_admin, login_url='accounts:login')
def news_create(request):
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save()
            messages.success(request, 'Actualite creee avec succes.')
            return redirect('public_site:news_manage_update', pk=news.pk)
    else:
        form = NewsForm()
    return render(request, 'public_site/news_manage_form.html', {
        'form': form,
        'title': 'Ajouter une actualite',
        'submit_label': 'Enregistrer',
    })


@user_passes_test(is_admin, login_url='accounts:login')
def news_update(request, pk):
    news = get_object_or_404(News, pk=pk)
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news)
        if form.is_valid():
            form.save()
            messages.success(request, 'Actualite mise a jour.')
            return redirect('public_site:news_manage_update', pk=news.pk)
    else:
        form = NewsForm(instance=news)
    return render(request, 'public_site/news_manage_form.html', {
        'form': form,
        'title': 'Modifier l actualite',
        'submit_label': 'Mettre a jour',
        'news': news,
    })


@user_passes_test(is_admin, login_url='accounts:login')
def news_delete(request, pk):
    news = get_object_or_404(News, pk=pk)
    if request.method == 'POST':
        news.delete()
        messages.success(request, 'Actualite supprimee.')
        return redirect('public_site:news_manage_list')
    return render(request, 'public_site/news_manage_confirm_delete.html', {
        'news': news,
    })


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST, user=request.user)
        if form.is_valid():
            contact_message = form.save(commit=False)
            if request.user.is_authenticated:
                contact_message.sender = request.user
            contact_message.save()
            messages.success(
                request,
                'Votre message a bien ete envoye. Vous pouvez suivre son traitement dans votre espace.',
            )
            return redirect('public_site:contact')
    else:
        form = ContactForm(user=request.user)
    return render(request, 'public_site/contact.html', {
        'form': form,
        'platform': _platform_info(),
    })
