import json

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from .models import (
    Ingredient, Cocktail, CocktailIngredient, Rating, Comment, UserProfile,
    INGREDIENT_CATEGORIES,
)
from .forms import RegisterForm, CocktailForm, CommentForm, ProfileForm
def make_user(username='testuser', password='testpass123'):
    return User.objects.create_user(username=username, password=password)
def make_cocktail(creator, name='Mojito', description='A classic', instructions='Mix it'):
    return Cocktail.objects.create(
        name=name,
        description=description,
        instructions=instructions,
        creator=creator,
    )
def make_ingredient(name='Rum', category='spirits'):
    return Ingredient.objects.create(name=name, category=category)


class IngredientModelTest(TestCase):

    def test_str(self):
        ing = make_ingredient('Lime Juice', 'mixers')
        self.assertEqual(str(ing), 'Lime Juice')

    def test_default_category(self):
        ing = Ingredient.objects.create(name='Mystery Herb')
        self.assertEqual(ing.category, 'other')

    def test_name_unique(self):
        make_ingredient('Vodka')
        with self.assertRaises(Exception):
            make_ingredient('Vodka')
    def test_ordering_by_name(self):
        make_ingredient('Zesty Lime', 'mixers')
        make_ingredient('Apple Juice', 'mixers')
        names = list(Ingredient.objects.values_list('name', flat=True))
        self.assertEqual(names, sorted(names))

class CocktailModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.cocktail = make_cocktail(self.user)
    def test_str(self):
        self.assertEqual(str(self.cocktail), 'Mojito')
    def test_avg_rating_no_ratings(self):
        self.assertEqual(self.cocktail.avg_rating(), 0)
    def test_avg_rating_with_ratings(self):
        user2 = make_user('user2')
        Rating.objects.create(user=self.user, cocktail=self.cocktail, stars=4)
        Rating.objects.create(user=user2, cocktail=self.cocktail, stars=2)
        self.assertEqual(self.cocktail.avg_rating(), 3.0)

    def test_rating_count(self):
        self.assertEqual(self.cocktail.rating_count(), 0)
        Rating.objects.create(user=self.user, cocktail=self.cocktail, stars=5)
        self.assertEqual(self.cocktail.rating_count(), 1)

    def test_avg_rating_rounds_to_one_decimal(self):
        users = [make_user(f'u{i}') for i in range(3)]
        for i, u in enumerate(users, start=1):
            Rating.objects.create(user=u, cocktail=self.cocktail, stars=i)
        # avg of 1,2,3 = 2.0 — just ensure it returns a float
        avg = self.cocktail.avg_rating()
        self.assertIsInstance(avg, float)

    def test_ordering_newest_first(self):
        c2 = make_cocktail(self.user, name='Daiquiri')
        cocktails = list(Cocktail.objects.all())
        self.assertEqual(cocktails[0], c2)
        self.assertEqual(cocktails[1], self.cocktail)


class CocktailIngredientModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.cocktail = make_cocktail(self.user)
        self.ingredient = make_ingredient('Rum')
        self.ci = CocktailIngredient.objects.create(
            cocktail=self.cocktail, ingredient=self.ingredient, amount='50ml'
        )

    def test_str(self):
        self.assertEqual(str(self.ci), '50ml Rum')

    def test_unique_together(self):
        with self.assertRaises(Exception):
            CocktailIngredient.objects.create(
                cocktail=self.cocktail, ingredient=self.ingredient, amount='100ml'
            )

class RatingModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.cocktail = make_cocktail(self.user)
    def test_str(self):
        rating = Rating.objects.create(user=self.user, cocktail=self.cocktail, stars=4)
        self.assertIn('testuser', str(rating))
        self.assertIn('Mojito', str(rating))
        self.assertIn('4', str(rating))
    def test_unique_together(self):
        Rating.objects.create(user=self.user, cocktail=self.cocktail, stars=3)
        with self.assertRaises(Exception):
            Rating.objects.create(user=self.user, cocktail=self.cocktail, stars=5)

    def test_update_or_create_replaces_rating(self):
        Rating.objects.update_or_create(
            user=self.user, cocktail=self.cocktail, defaults={'stars': 3}
        )
        Rating.objects.update_or_create(
            user=self.user, cocktail=self.cocktail, defaults={'stars': 5}
        )
        self.assertEqual(Rating.objects.get(user=self.user, cocktail=self.cocktail).stars, 5)


class CommentModelTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.cocktail = make_cocktail(self.user)

    def test_str(self):
        comment = Comment.objects.create(
            user=self.user, cocktail=self.cocktail, text='Delicious!'
        )
        self.assertIn('testuser', str(comment))
        self.assertIn('Mojito', str(comment))

    def test_ordering_newest_first(self):
        c1 = Comment.objects.create(user=self.user, cocktail=self.cocktail, text='First')
        user2 = make_user('user2')
        c2 = Comment.objects.create(user=user2, cocktail=self.cocktail, text='Second')
        comments = list(self.cocktail.comments.all())
        self.assertEqual(comments[0], c2)
        self.assertEqual(comments[1], c1)


class UserProfileModelTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)

    def test_str(self):
        self.assertIn('testuser', str(self.profile))

    def test_get_suggestions_no_ingredients(self):
        self.assertEqual(self.profile.get_suggestions(), [])

    def test_get_suggestions_with_matching_cocktail(self):
        rum = make_ingredient('Rum', 'spirits')
        lime = make_ingredient('Lime', 'mixers')
        mint = make_ingredient('Mint', 'garnishes')

        creator = make_user('creator')
        cocktail = make_cocktail(creator, 'Mojito')
        for ing, amt in [(rum, '50ml'), (lime, '1'), (mint, 'handful')]:
            CocktailIngredient.objects.create(cocktail=cocktail, ingredient=ing, amount=amt)

        self.profile.user_ingredients.set([rum, lime])
        suggestions = self.profile.get_suggestions()
        self.assertIn(cocktail, suggestions)
    def test_get_suggestions_insufficient_match(self):
        rum = make_ingredient('Rum', 'spirits')
        lime = make_ingredient('Lime', 'mixers')
        mint = make_ingredient('Mint', 'garnishes')
        sugar = make_ingredient('Sugar', 'syrups')

        creator = make_user('creator')
        cocktail = make_cocktail(creator, 'Mojito')
        for ing, amt in [(rum, '50ml'), (lime, '1'), (mint, 'handful'), (sugar, '1tsp')]:
            CocktailIngredient.objects.create(cocktail=cocktail, ingredient=ing, amount=amt)

        self.profile.user_ingredients.set([rum])
        suggestions = self.profile.get_suggestions()
        self.assertNotIn(cocktail, suggestions)
    def test_get_suggestions_max_ten(self):
        creator = make_user('creator')
        shared_ing = make_ingredient('Vodka', 'spirits')
        self.profile.user_ingredients.set([shared_ing])
        for i in range(15):
            ing2 = make_ingredient(f'Extra{i}', 'other')
            c = make_cocktail(creator, name=f'Drink{i}')
            CocktailIngredient.objects.create(cocktail=c, ingredient=shared_ing, amount='50ml')
            CocktailIngredient.objects.create(cocktail=c, ingredient=ing2, amount='10ml')
        suggestions = self.profile.get_suggestions()
        self.assertLessEqual(len(suggestions), 10)
class RegisterFormTest(TestCase):

    def _valid_data(self):
        return {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'str0ng!Pass99',
            'password2': 'str0ng!Pass99',
        }

    def test_valid_form(self):
        form = RegisterForm(data=self._valid_data())
        self.assertTrue(form.is_valid())
    def test_missing_email(self):
        data = self._valid_data()
        data['email'] = ''
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_password_mismatch(self):
        data = self._valid_data()
        data['password2'] = 'different'
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_duplicate_username(self):
        make_user('newuser')
        form = RegisterForm(data=self._valid_data())
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_all_fields_have_form_control_class(self):
        form = RegisterForm()
        for name, field in form.fields.items():
            self.assertIn('form-control', field.widget.attrs.get('class', ''),
                          msg=f"Field '{name}' missing form-control class")


class CocktailFormTest(TestCase):

    def test_valid_form(self):
        form = CocktailForm(data={
            'name': 'Negroni',
            'description': 'Bitter and sweet.',
            'instructions': 'Stir over ice.',
        })
        self.assertTrue(form.is_valid())

    def test_missing_name(self):
        form = CocktailForm(data={
            'description': 'No name here.',
            'instructions': 'Steps.',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_missing_description(self):
        form = CocktailForm(data={
            'name': 'Negroni',
            'instructions': 'Stir.',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)


class CommentFormTest(TestCase):

    def test_valid_form(self):
        form = CommentForm(data={'text': 'Great cocktail!'})
        self.assertTrue(form.is_valid())

    def test_empty_text(self):
        form = CommentForm(data={'text': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)


class ProfileFormTest(TestCase):

    def test_valid_form_blank_bio(self):
        form = ProfileForm(data={'bio': ''})
        self.assertTrue(form.is_valid())

    def test_valid_form_with_bio(self):
        form = ProfileForm(data={'bio': 'I love cocktails.'})
        self.assertTrue(form.is_valid())

class HomeViewTest(TestCase):
    def test_home_returns_200(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
    def test_home_context_keys(self):
        response = self.client.get(reverse('home'))
        for key in ('featured', 'recent', 'popular_ingredients',
                    'total_cocktails', 'total_ingredients'):
            self.assertIn(key, response.context)


class BrowseViewTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.c1 = make_cocktail(self.user, name='Mojito', description='rum mint lime')
        self.c2 = make_cocktail(self.user, name='Negroni', description='bitter orange')

    def test_browse_returns_200(self):
        response = self.client.get(reverse('browse'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cocktails/browse.html')

    def test_browse_search_filters_by_name(self):
        response = self.client.get(reverse('browse'), {'q': 'Mojito'})
        self.assertEqual(response.status_code, 200)
        names = [c.name for c in response.context['cocktails']]
        self.assertIn('Mojito', names)
        self.assertNotIn('Negroni', names)

    def test_browse_search_filters_by_description(self):
        response = self.client.get(reverse('browse'), {'q': 'bitter'})
        names = [c.name for c in response.context['cocktails']]
        self.assertIn('Negroni', names)
        self.assertNotIn('Mojito', names)

    def test_browse_sort_by_rating(self):
        response = self.client.get(reverse('browse'), {'sort': 'rating'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sort'], 'rating')
    def test_browse_sort_by_popular(self):
        response = self.client.get(reverse('browse'), {'sort': 'popular'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sort'], 'popular')
    def test_browse_filter_by_ingredient(self):
        rum = make_ingredient('Rum')
        CocktailIngredient.objects.create(cocktail=self.c1, ingredient=rum, amount='50ml')
        response = self.client.get(reverse('browse'), {'ingredients': str(rum.id)})
        names = [c.name for c in response.context['cocktails']]
        self.assertIn('Mojito', names)
        self.assertNotIn('Negroni', names)


class CocktailDetailViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.cocktail = make_cocktail(self.user)

    def test_detail_anonymous(self):
        response = self.client.get(reverse('cocktail_detail', args=[self.cocktail.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cocktails/detail.html')
    def test_detail_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cocktail_detail', args=[self.cocktail.pk]))
        self.assertEqual(response.status_code, 200)

    def test_detail_404_on_missing(self):
        response = self.client.get(reverse('cocktail_detail', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_detail_context_keys(self):
        response = self.client.get(reverse('cocktail_detail', args=[self.cocktail.pk]))
        for key in ('cocktail', 'user_rating', 'is_favourite', 'comments', 'comment_form', 'related'):
            self.assertIn(key, response.context)


class CocktailCreateViewTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_create_redirects_anonymous(self):
        response = self.client.get(reverse('cocktail_create'))
        self.assertRedirects(response, '/login/?next=/cocktails/create/')

    def test_create_get_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cocktail_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cocktails/create.html')

    def test_create_post_valid(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('cocktail_create'), {
            'name': 'Aperol Spritz',
            'description': 'Italian classic.',
            'instructions': 'Pour Aperol, add prosecco, top with soda.',
        })
        self.assertEqual(Cocktail.objects.filter(name='Aperol Spritz').count(), 1)
        cocktail = Cocktail.objects.get(name='Aperol Spritz')
        self.assertRedirects(response, reverse('cocktail_detail', args=[cocktail.pk]))

    def test_create_post_invalid_stays_on_form(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('cocktail_create'), {
            'name': '',
            'description': '',
            'instructions': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'name', 'This field is required.')

    def test_create_sets_creator(self):
        self.client.login(username='testuser', password='testpass123')
        self.client.post(reverse('cocktail_create'), {
            'name': 'Test Drink',
            'description': 'Desc.',
            'instructions': 'Do stuff.',
        })
        cocktail = Cocktail.objects.get(name='Test Drink')
        self.assertEqual(cocktail.creator, self.user)

    def test_create_with_ingredients(self):
        self.client.login(username='testuser', password='testpass123')
        self.client.post(reverse('cocktail_create'), {
            'name': 'Custom Drink',
            'description': 'Desc.',
            'instructions': 'Mix.',
            'ingredient_name[]': ['Vodka', 'Tonic'],
            'ingredient_amount[]': ['50ml', '100ml'],
        })
        cocktail = Cocktail.objects.get(name='Custom Drink')
        self.assertEqual(cocktail.cocktail_ingredients.count(), 2)


class CocktailEditViewTest(TestCase):

    def setUp(self):
        self.owner = make_user('owner')
        self.other = make_user('other')
        self.cocktail = make_cocktail(self.owner)

    def test_edit_redirects_anonymous(self):
        url = reverse('cocktail_edit', args=[self.cocktail.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_edit_get_as_owner(self):
        self.client.login(username='owner', password='testpass123')
        response = self.client.get(reverse('cocktail_edit', args=[self.cocktail.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cocktails/edit.html')

    def test_edit_blocked_for_non_owner(self):
        self.client.login(username='other', password='testpass123')
        response = self.client.get(reverse('cocktail_edit', args=[self.cocktail.pk]))
        self.assertRedirects(response, reverse('cocktail_detail', args=[self.cocktail.pk]))

    def test_edit_post_updates_cocktail(self):
        self.client.login(username='owner', password='testpass123')
        self.client.post(reverse('cocktail_edit', args=[self.cocktail.pk]), {
            'name': 'Updated Mojito',
            'description': 'New description.',
            'instructions': 'New steps.',
        })
        self.cocktail.refresh_from_db()
        self.assertEqual(self.cocktail.name, 'Updated Mojito')

    def test_staff_can_edit_any_cocktail(self):
        staff = User.objects.create_user('staff', password='testpass123', is_staff=True)
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('cocktail_edit', args=[self.cocktail.pk]))
        self.assertEqual(response.status_code, 200)


class CocktailDeleteViewTest(TestCase):
    def setUp(self):
        self.owner = make_user('owner')
        self.other = make_user('other')
        self.cocktail = make_cocktail(self.owner)
    def test_delete_blocked_for_non_owner(self):
        self.client.login(username='other', password='testpass123')
        self.client.post(reverse('cocktail_delete', args=[self.cocktail.pk]))
        self.assertTrue(Cocktail.objects.filter(pk=self.cocktail.pk).exists())
    def test_delete_by_owner(self):
        self.client.login(username='owner', password='testpass123')
        self.client.post(reverse('cocktail_delete', args=[self.cocktail.pk]))
        self.assertFalse(Cocktail.objects.filter(pk=self.cocktail.pk).exists())

    def test_delete_requires_post(self):
        self.client.login(username='owner', password='testpass123')
        response = self.client.get(reverse('cocktail_delete', args=[self.cocktail.pk]))
        self.assertEqual(response.status_code, 405)

    def test_staff_can_delete_any_cocktail(self):
        staff = User.objects.create_user('staff', password='testpass123', is_staff=True)
        self.client.login(username='staff', password='testpass123')
        self.client.post(reverse('cocktail_delete', args=[self.cocktail.pk]))
        self.assertFalse(Cocktail.objects.filter(pk=self.cocktail.pk).exists())

class RateCocktailViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.cocktail = make_cocktail(self.user)
        self.url = reverse('rate_cocktail', args=[self.cocktail.pk])
    def _post(self, stars):
        return self.client.post(
            self.url,
            data=json.dumps({'stars': stars}),
            content_type='application/json',
        )
    def test_rate_requires_login(self):
        response = self._post(4)
        self.assertEqual(response.status_code, 302)
    def test_rate_valid(self):
        self.client.login(username='testuser', password='testpass123')
        response = self._post(4)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['user_rating'], 4)

    def test_rate_invalid_stars_high(self):
        self.client.login(username='testuser', password='testpass123')
        response = self._post(6)
        self.assertEqual(response.status_code, 400)

    def test_rate_invalid_stars_low(self):
        self.client.login(username='testuser', password='testpass123')
        response = self._post(0)
        self.assertEqual(response.status_code, 400)

    def test_rate_updates_existing(self):
        self.client.login(username='testuser', password='testpass123')
        self._post(3)
        response = self._post(5)
        data = response.json()
        self.assertEqual(data['user_rating'], 5)
        self.assertEqual(Rating.objects.filter(cocktail=self.cocktail).count(), 1)

    def test_rate_returns_avg_and_count(self):
        self.client.login(username='testuser', password='testpass123')
        response = self._post(4)
        data = response.json()
        self.assertIn('avg_rating', data)
        self.assertIn('rating_count', data)

    def test_rate_invalid_json(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            self.url, data='not json', content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)


class AddCommentViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.cocktail = make_cocktail(self.user)
        self.url = reverse('add_comment', args=[self.cocktail.pk])
    def test_add_comment_requires_login(self):
        response = self.client.post(self.url, {'text': 'Nice!'})
        self.assertEqual(response.status_code, 302)
    def test_add_comment_valid(self):
        self.client.login(username='testuser', password='testpass123')
        self.client.post(self.url, {'text': 'Delicious!'})
        self.assertEqual(Comment.objects.filter(cocktail=self.cocktail).count(), 1)

    def test_add_comment_ajax_returns_json(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            self.url, {'text': 'Great!'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['comment']['text'], 'Great!')

    def test_add_comment_sets_user_and_cocktail(self):
        self.client.login(username='testuser', password='testpass123')
        self.client.post(self.url, {'text': 'Yummy!'})
        comment = Comment.objects.get(cocktail=self.cocktail)
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.cocktail, self.cocktail)


class DeleteCommentViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.other = make_user('other')
        self.cocktail = make_cocktail(self.user)
        self.comment = Comment.objects.create(
            user=self.user, cocktail=self.cocktail, text='Hello'
        )
        self.url = reverse('delete_comment', args=[self.cocktail.pk, self.comment.pk])
    def test_delete_own_comment(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.url)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())
    def test_delete_other_comment_denied(self):
        self.client.login(username='other', password='testpass123')
        response = self.client.post(
            self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())
    def test_delete_ajax_returns_json(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

    def test_staff_can_delete_any_comment(self):
        staff = User.objects.create_user('staff', password='testpass123', is_staff=True)
        self.client.login(username='staff', password='testpass123')
        self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())


class ToggleFavouriteViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.cocktail = make_cocktail(self.user)
        self.url = reverse('toggle_favourite', args=[self.cocktail.pk])
    def test_toggle_requires_login(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
    def test_add_favourite(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.url)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_favourite'])
    def test_remove_favourite(self):
        self.client.login(username='testuser', password='testpass123')
        self.client.post(self.url)   # add
        response = self.client.post(self.url)  # remove
        data = response.json()
        self.assertFalse(data['is_favourite'])

    def test_toggle_creates_profile_if_missing(self):
        # No profile exists yet
        self.client.login(username='testuser', password='testpass123')
        UserProfile.objects.filter(user=self.user).delete()
        self.client.post(self.url)
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())


class ProfileViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
    def test_profile_returns_200(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')

    def test_profile_context_keys(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile'))
        for key in ('profile', 'user_cocktails', 'favourites', 'suggestions', 'all_ingredients'):
            self.assertIn(key, response.context)




class LoginViewTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_login_page_returns_200(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/auth.html')

    def test_authenticated_user_redirected_from_login(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('login'))
        self.assertRedirects(response, reverse('home'))

    def test_login_success(self):
        response = self.client.post(reverse('login'), {
            'form_type': 'login',
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertRedirects(response, '/')

    def test_login_invalid_credentials(self):
        response = self.client.post(reverse('login'), {
            'form_type': 'login',
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('login_error', response.context)
        self.assertIsNotNone(response.context['login_error'])

    def test_register_success(self):
        response = self.client.post(reverse('login'), {
            'form_type': 'register',
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'str0ng!Pass99',
            'password2': 'str0ng!Pass99',
        })
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_invalid_shows_errors(self):
        response = self.client.post(reverse('login'), {
            'form_type': 'register',
            'username': '',
            'email': 'bad-email',
            'password1': 'pass',
            'password2': 'different',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['register_form'].is_valid())

    def test_register_redirects_route(self):
        response = self.client.get(reverse('register'))
        self.assertRedirects(response, '/login/?tab=register')


class LogoutViewTest(TestCase):
    def test_logout_logs_out_user(self):
        make_user()
        self.client.login(username='testuser', password='testpass123')
        self.client.post(reverse('logout'))
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)

    def test_logout_requires_post(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 405)

    def test_logout_redirects_home(self):
        make_user()
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('home'))


class IngredientAutocompleteViewTest(TestCase):


    def setUp(self):
        make_ingredient('Rum', 'spirits')
        make_ingredient('Rosemary', 'garnishes')
        make_ingredient('Vodka', 'spirits')

    def test_autocomplete_short_query_returns_empty(self):
        response = self.client.get(reverse('ingredient_autocomplete'), {'q': 'R'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['results'], [])

    def test_autocomplete_returns_matches(self):
        response = self.client.get(reverse('ingredient_autocomplete'), {'q': 'Ru'})
        data = response.json()
        names = [r['name'] for r in data['results']]
        self.assertIn('Rum', names)
        self.assertNotIn('Vodka', names)

    def test_autocomplete_case_insensitive(self):
        response = self.client.get(reverse('ingredient_autocomplete'), {'q': 'rum'})
        data = response.json()
        names = [r['name'] for r in data['results']]
        self.assertIn('Rum', names)

    def test_autocomplete_result_shape(self):
        response = self.client.get(reverse('ingredient_autocomplete'), {'q': 'Vo'})
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        result = data['results'][0]
        self.assertIn('id', result)
        self.assertIn('name', result)

    def test_autocomplete_max_ten_results(self):
        for i in range(15):
            Ingredient.objects.get_or_create(name=f'Rum{i}')
        response = self.client.get(reverse('ingredient_autocomplete'), {'q': 'Rum'})
        data = response.json()
        self.assertLessEqual(len(data['results']), 10)
