
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shakesremix.settings')
django.setup()

from django.contrib.auth.models import User
from cocktails.models import Cocktail, Ingredient, CocktailIngredient, Rating, Comment, UserProfile

# --- Create users ---
users_data = [
    ('sophia', 'sophia@example.com', 'password123'),
    ('daniel', 'daniel@example.com', 'password123'),
    ('marco',  'marco@example.com',  'password123'),
]

users = {}
for uname, email, pwd in users_data:
    u, created = User.objects.get_or_create(username=uname, defaults={'email': email})
    if created:
        u.set_password(pwd)
        u.save()
        UserProfile.objects.get_or_create(user=u)
    users[uname] = u

# --- Ingredients with categories ---
ingredient_data = [
    ('Vodka', 'spirits'), ('Rum', 'spirits'), ('Gin', 'spirits'),
    ('Tequila', 'spirits'), ('Whiskey', 'spirits'), ('Triple Sec', 'spirits'),
    ('Blue Curacao', 'spirits'), ('Chambord', 'spirits'), ('Peach Schnapps', 'spirits'),
    ('Kahlua', 'spirits'), ('Baileys Irish Cream', 'spirits'), ('Vermouth', 'spirits'),
    ('Campari', 'spirits'), ('Aperol', 'spirits'),
    ('Soda Water', 'mixers'), ('Tonic Water', 'mixers'), ('Ginger Beer', 'mixers'),
    ('Orange Juice', 'mixers'), ('Cranberry Juice', 'mixers'), ('Pineapple Juice', 'mixers'),
    ('Prosecco', 'mixers'), ('Champagne', 'mixers'),
    ('Mint Leaves', 'garnishes'), ('Cucumber', 'garnishes'), ('Basil', 'garnishes'),
    ('Rosemary', 'garnishes'), ('Blackberries', 'garnishes'), ('Strawberries', 'garnishes'),
    ('Salt', 'garnishes'), ('Sugar', 'garnishes'),
    ('Lime Juice', 'syrups'), ('Lemon Juice', 'syrups'), ('Simple Syrup', 'syrups'),
    ('Grenadine', 'syrups'), ('Honey', 'syrups'), ('Coconut Cream', 'syrups'),
    ('Ice', 'other'), ('Egg White', 'other'), ('Angostura Bitters', 'other'),
]

ingredients = {}
for name, category in ingredient_data:
    ing, created = Ingredient.objects.get_or_create(name=name, defaults={'category': category})
    if not created and ing.category != category:
        ing.category = category
        ing.save()
    ingredients[name] = ing

# --- Cocktails ---
cocktails_data = [
    {
        'name': 'Classic Mojito',
        'creator': 'marco',
        'description': 'A refreshing Cuban classic made with fresh mint, lime, and rum. Perfect for hot summer days.',
        'instructions': '1. Muddle mint leaves and lime juice in a glass.\n2. Add simple syrup and rum.\n3. Fill with ice and top with soda water.\n4. Garnish with a sprig of mint and a lime wheel.',
        'ingredients': [
            ('Rum', '60ml'), ('Lime Juice', '30ml'), ('Simple Syrup', '15ml'),
            ('Mint Leaves', '10 leaves'), ('Soda Water', 'to top'), ('Ice', 'crushed'),
        ],
    },
    {
        'name': 'Aperol Spritz',
        'creator': 'sophia',
        'description': 'The quintessential Italian aperitivo. Light, bitter-sweet, and beautiful.',
        'instructions': '1. Fill a large wine glass with ice.\n2. Add Aperol.\n3. Top with Prosecco.\n4. Add a splash of soda water.\n5. Garnish with a slice of orange.',
        'ingredients': [
            ('Aperol', '60ml'), ('Prosecco', '90ml'), ('Soda Water', '30ml'), ('Ice', 'cubed'),
        ],
    },
    {
        'name': 'Espresso Martini',
        'creator': 'marco',
        'description': 'A chic cocktail combining the kick of coffee with smooth vodka and Kahlua.',
        'instructions': '1. Brew a strong espresso shot and let cool.\n2. Combine vodka, Kahlua, simple syrup and espresso in a shaker with ice.\n3. Shake vigorously until very cold.\n4. Double strain into a chilled martini glass.\n5. Garnish with three coffee beans.',
        'ingredients': [
            ('Vodka', '45ml'), ('Kahlua', '15ml'), ('Simple Syrup', '10ml'),
        ],
    },
    {
        'name': 'Margarita',
        'creator': 'sophia',
        'description': 'The timeless Mexican classic. Tangy, salty, and utterly satisfying.',
        'instructions': '1. Rim a glass with salt.\n2. Combine tequila, triple sec and lime juice in a shaker with ice.\n3. Shake well and strain into the prepared glass over fresh ice.\n4. Garnish with a lime wedge.',
        'ingredients': [
            ('Tequila', '50ml'), ('Triple Sec', '20ml'), ('Lime Juice', '25ml'), ('Salt', 'for rim'), ('Ice', 'cubed'),
        ],
    },
    {
        'name': 'Negroni',
        'creator': 'marco',
        'description': 'A bittersweet Italian classic that has stood the test of time. Beautifully balanced.',
        'instructions': '1. Combine gin, Campari and sweet vermouth in a mixing glass with ice.\n2. Stir for 30 seconds until chilled and diluted.\n3. Strain into an Old Fashioned glass over a large ice cube.\n4. Express orange peel over the glass and use as garnish.',
        'ingredients': [
            ('Gin', '30ml'), ('Campari', '30ml'), ('Vermouth', '30ml'), ('Ice', 'cubed'),
        ],
    },
    {
        'name': 'Piña Colada',
        'creator': 'daniel',
        'description': 'A tropical escape in a glass. Creamy, sweet, and perfect for sipping by the pool.',
        'instructions': '1. Blend rum, coconut cream, and pineapple juice with a cup of ice.\n2. Blend until smooth and creamy.\n3. Pour into a chilled glass.\n4. Garnish with a pineapple wedge and a maraschino cherry.',
        'ingredients': [
            ('Rum', '60ml'), ('Coconut Cream', '60ml'), ('Pineapple Juice', '120ml'), ('Ice', 'crushed'),
        ],
    },
    {
        'name': 'Moscow Mule',
        'creator': 'daniel',
        'description': 'A spicy, refreshing drink traditionally served in a copper mug. Simple and satisfying.',
        'instructions': '1. Fill a copper mug (or glass) with ice.\n2. Add vodka and lime juice.\n3. Top with ginger beer.\n4. Garnish with a lime wheel and a sprig of mint.',
        'ingredients': [
            ('Vodka', '45ml'), ('Ginger Beer', '120ml'), ('Lime Juice', '15ml'), ('Mint Leaves', 'for garnish'), ('Ice', 'cubed'),
        ],
    },
    {
        'name': 'Whiskey Sour',
        'creator': 'marco',
        'description': 'A classic sour cocktail with a beautiful frothy top from egg white. Sophisticated and delicious.',
        'instructions': '1. Add whiskey, lemon juice, simple syrup and egg white to a shaker.\n2. Dry shake (without ice) vigorously for 15 seconds.\n3. Add ice and shake again until very cold.\n4. Strain into a rocks glass over fresh ice.\n5. Add a few drops of Angostura bitters on the foam.',
        'ingredients': [
            ('Whiskey', '45ml'), ('Lemon Juice', '22ml'), ('Simple Syrup', '15ml'),
            ('Egg White', '1'), ('Angostura Bitters', '2 dashes'),
        ],
    },
    {
        'name': 'Cosmopolitan',
        'creator': 'sophia',
        'description': 'Made famous by Sex and the City, this elegant pink cocktail is as chic as they come.',
        'instructions': '1. Combine vodka, triple sec, cranberry juice and lime juice in a shaker with ice.\n2. Shake vigorously until well chilled.\n3. Strain into a chilled cocktail glass.\n4. Garnish with a flamed orange twist.',
        'ingredients': [
            ('Vodka', '40ml'), ('Triple Sec', '15ml'), ('Cranberry Juice', '30ml'), ('Lime Juice', '15ml'),
        ],
    },
    {
        'name': "Dark 'n' Stormy",
        'creator': 'daniel',
        'description': "Bermuda's national drink. Deep, spicy and refreshing all at once.",
        'instructions': '1. Fill a tall glass with ice.\n2. Add dark rum.\n3. Top with ginger beer.\n4. Garnish with a lime wedge and do not stir – let the rum float on top.',
        'ingredients': [
            ('Rum', '60ml'), ('Ginger Beer', '120ml'), ('Lime Juice', '10ml'), ('Ice', 'cubed'),
        ],
    },
    {
        'name': 'Tom Collins',
        'creator': 'sophia',
        'description': 'A tall, refreshing gin-based drink perfect for warm weather entertaining.',
        'instructions': '1. Combine gin, lemon juice and simple syrup in a shaker with ice.\n2. Shake and strain into a Collins glass filled with fresh ice.\n3. Top with soda water.\n4. Garnish with a lemon slice and a maraschino cherry.',
        'ingredients': [
            ('Gin', '45ml'), ('Lemon Juice', '22ml'), ('Simple Syrup', '15ml'), ('Soda Water', 'to top'), ('Ice', 'cubed'),
        ],
    },
    {
        'name': 'Strawberry Daiquiri',
        'creator': 'daniel',
        'description': 'A fruity, frozen twist on the classic daiquiri. Summery and crowd-pleasing.',
        'instructions': '1. Add rum, lime juice, simple syrup and fresh strawberries to a blender.\n2. Add a cup of ice and blend until smooth.\n3. Pour into a chilled glass.\n4. Garnish with a fresh strawberry on the rim.',
        'ingredients': [
            ('Rum', '60ml'), ('Lime Juice', '25ml'), ('Simple Syrup', '20ml'),
            ('Strawberries', '5-6 fresh'), ('Ice', 'crushed'),
        ],
    },
]

for cd in cocktails_data:
    if Cocktail.objects.filter(name=cd['name']).exists():
        continue
    c = Cocktail.objects.create(
        name=cd['name'],
        creator=users[cd['creator']],
        description=cd['description'],
        instructions=cd['instructions'],
    )
    for ing_name, amount in cd['ingredients']:
        ing, _ = Ingredient.objects.get_or_create(name=ing_name)
        CocktailIngredient.objects.get_or_create(cocktail=c, ingredient=ing, defaults={'amount': amount})
    print(f'Created: {c.name}')

# Add ratings
cocktails = Cocktail.objects.all()
rater_pairs = [
    ('sophia', 5), ('daniel', 4), ('marco', 5),
]
all_users = list(users.values())

for i, c in enumerate(cocktails):
    for j, u in enumerate(all_users):
        stars = 4 + ((i + j) % 2)
        Rating.objects.get_or_create(user=u, cocktail=c, defaults={'stars': min(stars, 5)})

# Add comments
sample_comments = [
    "Made this last night and it was a huge hit at the party!",
    "Perfect recipe, I've tried many versions and this is the best.",
    "Great balance of flavours. I reduced the sugar slightly.",
    "So easy to make. My go-to recipe now!",
    "Brilliant! Added a splash of elderflower cordial too.",
]
for i, c in enumerate(cocktails[:6]):
    u = all_users[i % len(all_users)]
    Comment.objects.get_or_create(
        user=u, cocktail=c,
        defaults={'text': sample_comments[i % len(sample_comments)]},
    )

print("\nSeed data complete!")
print("Superuser: admin / admin123")
print("Users: sophia, daniel, marco (password: password123)")
