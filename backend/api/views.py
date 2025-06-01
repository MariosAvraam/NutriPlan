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
from .meal_planner_logic import generate_daily_meal_plan_v1
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
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found. Please set up your profile."}, status=status.HTTP_404_NOT_FOUND)

        logger.info(
            f"Meal plan generation requested for user: {request.user.username}")

        generated_data = generate_daily_meal_plan_v1(user_profile)

        if not generated_data:
            return Response({"error": "Could not generate a suitable meal plan with the current recipes and your targets. Try adjusting targets or check back later as more recipes are added."}, status=status.HTTP_400_BAD_REQUEST)

        # Serialize the plan for the response
        # The plan_recipes dict contains Recipe model instances
        serialized_meals = {}
        for meal_type, recipe_obj in generated_data["plan_recipes"].items():
            if recipe_obj:
                serialized_meals[meal_type] = RecipeSerializer(recipe_obj).data
            else:
                serialized_meals[meal_type] = None

        api_response_plan = {
            # Already in a good format
            "daily_targets": generated_data["user_targets"],
            "meals": serialized_meals,
            "totals_for_the_day": generated_data["plan_totals"]
        }

        return Response(api_response_plan, status=status.HTTP_200_OK)

# --- Optional: Ingredient List View (if you want to expose ingredients directly) ---
# class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = Ingredient.objects.all().order_by('name')
#     serializer_class = IngredientSerializer
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly]
