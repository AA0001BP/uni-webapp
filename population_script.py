import os
import sys
import django
import requests
from django.core.files.base import ContentFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shakesremix.settings')
django.setup()

from django.contrib.auth.models import User
from cocktails.models import (
    Cocktail, Ingredient, CocktailIngredient, Rating, Comment, UserProfile,
    INGREDIENT_CATEGORIES
)


def fetch_cocktail(name):
    url = f'https://www.thecocktaildb.com/api/json/v1/1/search.php?s={name}'
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('drinks'):
            return data['drinks'][0]
    except Exception as e:
        print(f'  API error for "{name}": {e}')
    return None


def download_image(url, filename):
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return ContentFile(r.content), filename
    except Exception as e:
        print(f'  Image download error: {e}')
    return None, None


def categorise(name):
    name_lower = name.lower()
    spirits = ['vodka', 'rum', 'gin', 'tequila', 'whiskey', 'whisky', 'bourbon',
               'brandy', 'triple sec', 'cointreau', 'campari', 'aperol', 'vermouth',
               'kahlua', 'baileys', 'schnapps', 'curacao', 'chambord', 'absinthe']
    mixers  = ['juice', 'soda', 'water', 'tonic', 'beer', 'wine', 'prosecco',
               'champagne', 'cider', 'cola', 'ginger beer', 'sprite', 'lemonade']
    garnish = ['mint', 'lime', 'lemon', 'orange', 'cherry', 'olive', 'salt',
               'sugar', 'cucumber', 'basil', 'rosemary']
    syrups  = ['syrup', 'honey', 'grenadine', 'cream', 'coconut']

    for s in spirits:
        if s in name_lower:
            return 'spirits'
    for m in mixers:
        if m in name_lower:
            return 'mixers'
    for g in garnish:
        if g in name_lower:
            return 'garnishes'
    for s in syrups:
        if s in name_lower:
            return 'syrups'
    return 'other'



print('Creating users...')

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@shakesremix.com', 'admin123')
    print('  Created superuser: admin / admin123')

sample_users = [
    ('sophia', 'sophia@example.com', 'Password123'),
    ('marco',  'marco@example.com',  'Password123'),
    ('daniel', 'daniel@example.com', 'Password123'),
]

users = {}
for uname, email, pwd in sample_users:
    user, created = User.objects.get_or_create(
        username=uname, defaults={'email': email}
    )
    if created:
        user.set_password(pwd)
        user.save()
        print(f'  Created user: {uname}')
    UserProfile.objects.get_or_create(user=user)
    users[uname] = user


cocktails_to_fetch = [
    ('Mojito',          'sophia'),
    ('Margarita',       'marco'),
    ('Negroni',         'marco'),
    ('Cosmopolitan',    'sophia'),
    ('Pina Colada',     'daniel'),
    ('Espresso Martini','daniel'),
]

print('\nFetching cocktails from TheCocktailDB...')

for cocktail_name, creator_name in cocktails_to_fetch:

    if Cocktail.objects.filter(name__iexact=cocktail_name).exists():
        print(f'  "{cocktail_name}" already exists, skipping.')
        continue

    print(f'  Fetching "{cocktail_name}"...')
    drink = fetch_cocktail(cocktail_name)

    if not drink:
        print(f'  Could not fetch "{cocktail_name}", skipping.')
        continue

    creator = users.get(creator_name, users['sophia'])

    category  = drink.get('strCategory', '')
    glass     = drink.get('strGlass', '')
    desc_parts = [p for p in [category, glass] if p]
    description = ' — '.join(desc_parts) if desc_parts else cocktail_name

    cocktail = Cocktail(
        name=drink['strDrink'],
        description=description,
        instructions=drink.get('strInstructions', '').strip(),
        creator=creator,
    )

    thumb_url = drink.get('strDrinkThumb')
    if thumb_url:
        img_content, filename = download_image(
            thumb_url,
            f"{drink['strDrink'].lower().replace(' ', '_')}.jpg"
        )
        if img_content:
            cocktail.image.save(filename, img_content, save=False)
            print(f'    Image downloaded.')

    cocktail.save()

    for i in range(1, 16):
        ing_name = drink.get(f'strIngredient{i}')
        measure  = drink.get(f'strMeasure{i}') or ''
        if not ing_name or not ing_name.strip():
            break
        ing_name = ing_name.strip().title()
        measure  = measure.strip() or '—'

        ing_qs = Ingredient.objects.filter(name__iexact=ing_name)
        if ing_qs.exists():
            ingredient = ing_qs.first()
        else:
            ingredient = Ingredient.objects.create(
                name=ing_name,
                category=categorise(ing_name)
            )

        CocktailIngredient.objects.get_or_create(
            cocktail=cocktail,
            ingredient=ingredient,
            defaults={'amount': measure}
        )

    print(f'  Created: {cocktail.name}')



print('\nAdding ratings...')

all_cocktails = list(Cocktail.objects.all())
all_users     = list(User.objects.filter(username__in=['sophia', 'marco', 'daniel']))

ratings_data = [4, 5, 5, 4, 3, 5]
for idx, cocktail in enumerate(all_cocktails):
    for j, user in enumerate(all_users):
        stars = ratings_data[(idx + j) % len(ratings_data)]
        Rating.objects.get_or_create(
            user=user, cocktail=cocktail,
            defaults={'stars': min(stars, 5)}
        )


print('Adding comments...')

comments_text = [
    'Made this last weekend and it was a huge hit!',
    'Perfect balance of flavours, will definitely make again.',
    'Really easy to follow, great for beginners.',
    'I added a bit more lime juice and it was even better.',
    'Classic recipe, exactly what I was looking for.',
]

for idx, cocktail in enumerate(all_cocktails[:5]):
    user = all_users[idx % len(all_users)]
    Comment.objects.get_or_create(
        user=user, cocktail=cocktail,
        defaults={'text': comments_text[idx % len(comments_text)]}
    )


print('\nPopulation complete!')
print('-------------------------------')
print('Superuser : admin / admin123')
print('Users     : sophia, marco, daniel  (password: Password123)')
print(f'Cocktails : {Cocktail.objects.count()}')
print(f'Ingredients: {Ingredient.objects.count()}')
