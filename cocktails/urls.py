from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cocktails/', views.browse, name='browse'),
    path('cocktails/create/', views.cocktail_create, name='cocktail_create'),
    path('cocktails/<int:pk>/', views.cocktail_detail, name='cocktail_detail'),
    path('cocktails/<int:pk>/edit/', views.cocktail_edit, name='cocktail_edit'),
    path('cocktails/<int:pk>/delete/', views.cocktail_delete, name='cocktail_delete'),
    path('cocktails/<int:pk>/rate/', views.rate_cocktail, name='rate_cocktail'),
    path('cocktails/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('cocktails/<int:pk>/comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('cocktails/<int:pk>/favourite/', views.toggle_favourite, name='toggle_favourite'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/ingredients/', views.ingredient_autocomplete, name='ingredient_autocomplete'),
]
