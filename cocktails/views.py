import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator

from .models import Cocktail, Ingredient, CocktailIngredient, Rating, Comment, UserProfile
from .forms import CocktailForm, RegisterForm, CommentForm, ProfileForm


def home(request):
    featured = Cocktail.objects.annotate(
        avg=Avg('ratings__stars'), num_ratings=Count('ratings')
    ).order_by('-avg', '-num_ratings')[:6]
    recent = Cocktail.objects.order_by('-created_at')[:6]
    popular_ingredients = Ingredient.objects.annotate(
        count=Count('cocktails')
    ).order_by('-count')[:12]
    total_cocktails = Cocktail.objects.count()
    total_users = Ingredient.objects.count()
    return render(request, 'home.html', {
        'featured': featured,
        'recent': recent,
        'popular_ingredients': popular_ingredients,
        'total_cocktails': total_cocktails,
        'total_ingredients': total_users,
    })


def browse(request):
    cocktails = Cocktail.objects.annotate(
        avg_stars=Avg('ratings__stars'),
        num_ratings=Count('ratings'),
    )

    q = request.GET.get('q', '').strip()
    if q:
        cocktails = cocktails.filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        )

    ingredient_ids = request.GET.getlist('ingredients')
    selected_ingredient_ids = []
    for ing_id in ingredient_ids:
        if ing_id.isdigit():
            cocktails = cocktails.filter(ingredients__id=int(ing_id))
            selected_ingredient_ids.append(int(ing_id))

    sort = request.GET.get('sort', 'newest')
    if sort == 'rating':
        cocktails = cocktails.order_by('-avg_stars', '-created_at')
    elif sort == 'popular':
        cocktails = cocktails.order_by('-num_ratings', '-created_at')
    else:
        cocktails = cocktails.order_by('-created_at')

    paginator = Paginator(cocktails.distinct(), 12)
    page = request.GET.get('page', 1)
    cocktails_page = paginator.get_page(page)

    all_ingredients = Ingredient.objects.annotate(
        count=Count('cocktails')
    ).order_by('category', 'name')

    # Group ingredients by category for sidebar
    from collections import defaultdict
    from .models import INGREDIENT_CATEGORIES
    cat_map = dict(INGREDIENT_CATEGORIES)
    grouped = defaultdict(list)
    for ing in all_ingredients:
        grouped[ing.category].append(ing)
    # Build ordered list of (label, ingredients) skipping empty categories
    category_order = [k for k, _ in INGREDIENT_CATEGORIES]
    grouped_ingredients = [
        (cat_map[cat], grouped[cat])
        for cat in category_order
        if grouped[cat]
    ]

    return render(request, 'cocktails/browse.html', {
        'cocktails': cocktails_page,
        'ingredients': all_ingredients,
        'grouped_ingredients': grouped_ingredients,
        'selected_ingredients': selected_ingredient_ids,
        'q': q,
        'sort': sort,
    })


def cocktail_detail(request, pk):
    cocktail = get_object_or_404(Cocktail, pk=pk)
    user_rating = None
    is_favourite = False

    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(user=request.user, cocktail=cocktail).first()
        try:
            is_favourite = request.user.profile.favourites.filter(id=cocktail.id).exists()
        except UserProfile.DoesNotExist:
            pass

    comments = cocktail.comments.select_related('user').all()
    comment_form = CommentForm()

    related = Cocktail.objects.filter(
        ingredients__in=cocktail.ingredients.all()
    ).exclude(pk=pk).distinct().order_by('-created_at')[:4]

    return render(request, 'cocktails/detail.html', {
        'cocktail': cocktail,
        'user_rating': user_rating,
        'is_favourite': is_favourite,
        'comments': comments,
        'comment_form': comment_form,
        'related': related,
    })


def _save_ingredients(request, cocktail):
    names = request.POST.getlist('ingredient_name[]')
    amounts = request.POST.getlist('ingredient_amount[]')
    for name, amount in zip(names, amounts):
        name = name.strip()
        amount = amount.strip()
        if name:
            qs = Ingredient.objects.filter(name__iexact=name)
            if qs.exists():
                ingredient = qs.first()
            else:
                ingredient = Ingredient.objects.create(name=name.title())
            CocktailIngredient.objects.get_or_create(
                cocktail=cocktail, ingredient=ingredient,
                defaults={'amount': amount or '—'},
            )


@login_required
def cocktail_create(request):
    if request.method == 'POST':
        form = CocktailForm(request.POST, request.FILES)
        if form.is_valid():
            cocktail = form.save(commit=False)
            cocktail.creator = request.user
            cocktail.save()
            _save_ingredients(request, cocktail)
            messages.success(request, 'Cocktail created successfully!')
            return redirect('cocktail_detail', pk=cocktail.pk)
    else:
        form = CocktailForm()
    return render(request, 'cocktails/create.html', {'form': form})


@login_required
def cocktail_edit(request, pk):
    cocktail = get_object_or_404(Cocktail, pk=pk)
    if cocktail.creator != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this cocktail.')
        return redirect('cocktail_detail', pk=pk)

    if request.method == 'POST':
        form = CocktailForm(request.POST, request.FILES, instance=cocktail)
        if form.is_valid():
            cocktail = form.save()
            cocktail.cocktail_ingredients.all().delete()
            _save_ingredients(request, cocktail)
            messages.success(request, 'Cocktail updated successfully!')
            return redirect('cocktail_detail', pk=cocktail.pk)
    else:
        form = CocktailForm(instance=cocktail)

    existing_ingredients = cocktail.cocktail_ingredients.select_related('ingredient').all()
    return render(request, 'cocktails/edit.html', {
        'form': form,
        'cocktail': cocktail,
        'existing_ingredients': existing_ingredients,
    })


@login_required
@require_POST
def cocktail_delete(request, pk):
    cocktail = get_object_or_404(Cocktail, pk=pk)
    if cocktail.creator != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete this cocktail.')
        return redirect('cocktail_detail', pk=pk)
    cocktail.delete()
    messages.success(request, 'Cocktail deleted.')
    return redirect('browse')


@login_required
@require_POST
def rate_cocktail(request, pk):
    cocktail = get_object_or_404(Cocktail, pk=pk)
    try:
        data = json.loads(request.body)
        stars = int(data.get('stars', 0))
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid data'}, status=400)

    if not 1 <= stars <= 5:
        return JsonResponse({'error': 'Stars must be between 1 and 5'}, status=400)

    Rating.objects.update_or_create(
        user=request.user, cocktail=cocktail,
        defaults={'stars': stars},
    )

    return JsonResponse({
        'success': True,
        'avg_rating': cocktail.avg_rating(),
        'rating_count': cocktail.rating_count(),
        'user_rating': stars,
    })


@login_required
@require_POST
def add_comment(request, pk):
    cocktail = get_object_or_404(Cocktail, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.cocktail = cocktail
        comment.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'text': comment.text,
                    'username': comment.user.username,
                    'created_at': comment.created_at.strftime('%b %d, %Y'),
                },
            })
        messages.success(request, 'Comment added.')
    return redirect('cocktail_detail', pk=pk)


@login_required
@require_POST
def delete_comment(request, pk, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, cocktail_id=pk)
    if comment.user != request.user and not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    comment.delete()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('cocktail_detail', pk=pk)


@login_required
@require_POST
def toggle_favourite(request, pk):
    cocktail = get_object_or_404(Cocktail, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.favourites.filter(id=cocktail.id).exists():
        profile.favourites.remove(cocktail)
        is_favourite = False
    else:
        profile.favourites.add(cocktail)
        is_favourite = True
    return JsonResponse({'success': True, 'is_favourite': is_favourite})


@login_required
def profile_view(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    user_cocktails = request.user.cocktails.annotate(
        avg=Avg('ratings__stars')
    ).order_by('-created_at')
    favourites = user_profile.favourites.annotate(
        avg=Avg('ratings__stars')
    ).order_by('-created_at')
    suggestions = user_profile.get_suggestions()
    all_ingredients = Ingredient.objects.order_by('name')

    return render(request, 'accounts/profile.html', {
        'profile': user_profile,
        'user_cocktails': user_cocktails,
        'favourites': favourites,
        'suggestions': suggestions,
        'all_ingredients': all_ingredients,
    })


@login_required
@require_POST
def update_profile(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST, request.FILES, instance=user_profile)
    if form.is_valid():
        form.save()
        ingredient_ids = request.POST.getlist('ingredient_ids[]')
        valid_ids = [i for i in ingredient_ids if i.isdigit()]
        user_profile.user_ingredients.set(
            Ingredient.objects.filter(id__in=valid_ids)
        )
        messages.success(request, 'Profile updated successfully!')
    return redirect('profile')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    register_form = RegisterForm()
    login_error = None
    active_tab = request.GET.get('tab', 'login')

    if request.method == 'POST':
        form_type = request.POST.get('form_type', 'login')

        if form_type == 'login':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect(request.GET.get('next', '/'))
            login_error = 'Invalid username or password.'
            active_tab = 'login'

        elif form_type == 'register':
            register_form = RegisterForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                UserProfile.objects.get_or_create(user=user)
                login(request, user)
                messages.success(request, f'Welcome to ShakesRemix, {user.username}!')
                return redirect('home')
            active_tab = 'register'

    return render(request, 'accounts/auth.html', {
        'register_form': register_form,
        'login_error': login_error,
        'active_tab': active_tab,
    })


def register(request):
    return redirect(f"/login/?tab=register")


@require_POST
def logout_view(request):
    logout(request)
    return redirect('home')


def ingredient_autocomplete(request):
    q = request.GET.get('q', '').strip()
    if len(q) >= 2:
        ingredients = Ingredient.objects.filter(name__icontains=q)[:10]
        data = [{'id': i.id, 'name': i.name} for i in ingredients]
    else:
        data = []
    return JsonResponse({'results': data})
