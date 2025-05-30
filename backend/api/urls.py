from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView,
    UserProfileView,
    RecipeViewSet,
    MealPlanGenerateView
    # Import IngredientViewSet if you created it
)
from .views import CustomAuthToken

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')
# router.register(r'ingredients', IngredientViewSet, basename='ingredient') # Uncomment if you have IngredientViewSet

# The API URLs are now determined automatically by the router.
# For simple views (not ViewSets), we define paths manually.
urlpatterns = [
    # Includes URLs for 'recipes' (and 'ingredients' if uncommented)
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', CustomAuthToken.as_view(), name='auth-login'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('mealplan/generate/', MealPlanGenerateView.as_view(),
         name='mealplan-generate'),

    # If you decide to use dj-rest-auth or djoser later for more complete auth:
    # path('auth/', include('dj_rest_auth.urls')),
    # path('auth/registration/', include('dj_rest_auth.registration.urls')), # For registration provided by dj-rest-auth
]
