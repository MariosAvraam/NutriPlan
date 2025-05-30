from .serializers import (
    UserSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    RecipeSerializer,
    # IngredientSerializer # If you want a direct endpoint for Ingredients
)
from .models import UserProfile, Recipe, Ingredient
from django.contrib.auth.models import User
from rest_framework import generics, viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
# For token authentication
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
import logging
logger = logging.getLogger(__name__)

# Add RecipeIngredient if you need a direct endpoint for it


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        # Optionally include user details in the login response
        # Assuming you have UserSerializer
        user_data = UserSerializer(user).data
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'email': user.email,  # Add any other user details you want
            'user_details': user_data
        })

# --- User Registration View ---


# generics.CreateAPIView is good for creation-only endpoints
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)  # Anyone can register
    serializer_class = RegisterSerializer

    # Optional: If you want to return user data or a token upon successful registration
    # def create(self, request, *args, **kwargs):
    #     response = super().create(request, *args, **kwargs)
    #     # You could create a token here or return user data
    #     # user = User.objects.get(username=response.data['username'])
    #     # token, created = Token.objects.get_or_create(user=user)
    #     # return Response({'token': token.key, 'user': response.data}, status=status.HTTP_201_CREATED)
    #     return response


# --- User Profile ViewSet ---
# A ViewSet is good if you want standard CRUD, but here we only need retrieve/update for the current user.
# So, a RetrieveUpdateAPIView might be more appropriate.
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    # Only authenticated users can access their profile
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Ensure users can only access/update their own profile
        # UserProfile is created via signal or in RegisterSerializer.create()
        profile, created = UserProfile.objects.get_or_create(
            user=self.request.user)
        return profile

    # Optional: If you need to do something special on update
    # def perform_update(self, serializer):
    #     serializer.save(user=self.request.user) # Ensure user is correctly associated if not read-only


# --- Recipe ViewSet (Read-Only for now) ---
# Provides .list() and .retrieve() actions
class RecipeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Recipe.objects.all().order_by(
        'name')  # Get all recipes, ordered by name
    serializer_class = RecipeSerializer
    # Allow anyone to view, but only auth users for other actions (if we add them)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # Add filtering or search backends later if needed
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # filterset_fields = ['meal_type']
    # search_fields = ['name', 'description', 'ingredients__name'] # Search by recipe name, description, or ingredient names
    # ordering_fields = ['name', 'total_calories']


# --- Meal Plan Generation View (Placeholder for now) ---
class MealPlanGenerateView(APIView):
    # Only authenticated users can generate plans
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # 1. Get UserProfile to access targets
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)

        target_calories = user_profile.target_calories
        # Convert percentages to grams (do this in the algorithm later)
        # target_protein_g = (target_calories * user_profile.target_protein_percent / 100) / 4
        # target_carbs_g = (target_calories * user_profile.target_carbs_percent / 100) / 4
        # target_fat_g = (target_calories * user_profile.target_fat_percent / 100) / 9

        # For now, return a dummy/placeholder plan
        # In Phase 4, this will call your meal generation algorithm
        logger.info(
            f"Meal plan generation requested for user: {request.user.username} with target calories: {target_calories}")

        # Dummy plan structure (replace with actual algorithm output later)
        # Fetch a few sample recipes to make it look somewhat real
        breakfast_recipe = Recipe.objects.filter(meal_type='breakfast').first()
        lunch_recipe = Recipe.objects.filter(meal_type='lunch').first()
        dinner_recipe = Recipe.objects.filter(meal_type='dinner').first()

        if not (breakfast_recipe and lunch_recipe and dinner_recipe):
            return Response({"error": "Not enough sample recipes to generate a dummy plan."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        dummy_plan = {
            "daily_targets": {
                "calories": target_calories,
                "protein_percent": user_profile.target_protein_percent,
                "carbs_percent": user_profile.target_carbs_percent,
                "fat_percent": user_profile.target_fat_percent,
            },
            "meals": {
                "breakfast": RecipeSerializer(breakfast_recipe).data if breakfast_recipe else None,
                "lunch": RecipeSerializer(lunch_recipe).data if lunch_recipe else None,
                "dinner": RecipeSerializer(dinner_recipe).data if dinner_recipe else None,
                "snacks": []  # Add snack logic later
            },
            "totals_for_the_day": {  # These would be calculated by the algorithm
                "calories": (breakfast_recipe.total_calories or 0) +
                            (lunch_recipe.total_calories or 0) +
                            (dinner_recipe.total_calories or 0),
                "protein_g": (breakfast_recipe.total_protein_g or 0) +
                             (lunch_recipe.total_protein_g or 0) +
                             (dinner_recipe.total_protein_g or 0),
                # ... and so on for carbs and fat
            }
        }
        return Response(dummy_plan, status=status.HTTP_200_OK)

# --- Optional: Ingredient List View (if you want to expose ingredients directly) ---
# class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = Ingredient.objects.all().order_by('name')
#     serializer_class = IngredientSerializer
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly]
