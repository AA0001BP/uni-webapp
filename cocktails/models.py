from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg


INGREDIENT_CATEGORIES = [
    ('spirits', 'Spirits'),
    ('mixers', 'Mixers'),
    ('garnishes', 'Garnishes'),
    ('syrups', 'Syrups & Sweeteners'),
    ('other', 'Other'),
]


class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(
        max_length=20, choices=INGREDIENT_CATEGORIES, default='other'
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Cocktail(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField()
    image = models.ImageField(upload_to='cocktails/', blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cocktails')
    ingredients = models.ManyToManyField(
        Ingredient, through='CocktailIngredient', related_name='cocktails'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def avg_rating(self):
        result = self.ratings.aggregate(avg=Avg('stars'))
        return round(result['avg'] or 0, 1)

    def rating_count(self):
        return self.ratings.count()

    class Meta:
        ordering = ['-created_at']


class CocktailIngredient(models.Model):
    cocktail = models.ForeignKey(
        Cocktail, on_delete=models.CASCADE, related_name='cocktail_ingredients'
    )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.amount} {self.ingredient.name}"

    class Meta:
        unique_together = ('cocktail', 'ingredient')


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    cocktail = models.ForeignKey(Cocktail, on_delete=models.CASCADE, related_name='ratings')
    stars = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'cocktail')

    def __str__(self):
        return f"{self.user.username} rated {self.cocktail.name}: {self.stars}/5"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    cocktail = models.ForeignKey(Cocktail, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} on {self.cocktail.name}"

    class Meta:
        ordering = ['-created_at']


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    favourites = models.ManyToManyField(Cocktail, blank=True, related_name='favourited_by')
    user_ingredients = models.ManyToManyField(
        Ingredient, blank=True, related_name='users_with'
    )

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_suggestions(self):
        if not self.user_ingredients.exists():
            return []

        user_ingredient_ids = set(self.user_ingredients.values_list('id', flat=True))
        suggestions = []

        for cocktail in Cocktail.objects.prefetch_related('cocktail_ingredients__ingredient'):
            cocktail_ingredient_ids = set(
                cocktail.cocktail_ingredients.values_list('ingredient_id', flat=True)
            )
            if not cocktail_ingredient_ids:
                continue
            match_count = len(user_ingredient_ids & cocktail_ingredient_ids)
            match_ratio = match_count / len(cocktail_ingredient_ids)
            if match_ratio >= 0.5:
                suggestions.append((cocktail, match_ratio))

        suggestions.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in suggestions[:10]]
