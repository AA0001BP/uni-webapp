from django.contrib import admin
from .models import Cocktail, Ingredient, CocktailIngredient, Rating, Comment, UserProfile


class CocktailIngredientInline(admin.TabularInline):
    model = CocktailIngredient
    extra = 1


@admin.register(Cocktail)
class CocktailAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'avg_rating', 'rating_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description', 'creator__username')
    inlines = [CocktailIngredientInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'cocktail', 'stars', 'created_at')
    list_filter = ('stars',)
    search_fields = ('user__username', 'cocktail__name')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'cocktail', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text', 'user__username', 'cocktail__name')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    filter_horizontal = ('favourites', 'user_ingredients')
    search_fields = ('user__username',)
