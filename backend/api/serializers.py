from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Ingredient, RecipeIngredient, Recipe


# --- User Serializers ---
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for basic User information (read-only for now).
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        # For security, make most fields read-only if this is just for display
        # read_only_fields = ['username', 'email']


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for User registration.
    Includes password validation and creation.
    """
    # Make password write-only (not included in response)
    password = serializers.CharField(write_only=True, required=True, style={
                                     'input_type': 'password'})
    # password2 = serializers.CharField(write_only=True, required=True, label="Confirm Password") # Optional confirm

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name']
        # extra_kwargs = {'password': {'write_only': True}} # Alternative way to set write_only

    def validate(self, attrs):
        # Add custom validation here if needed, e.g., password complexity,
        # or if using password2, ensure they match:
        # if attrs['password'] != attrs.pop('password2'): # .pop() to remove it from attrs
        #     raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            # Make email optional if desired
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        # UserProfile is created via signal or can create it here if not using signals
        # UserProfile.objects.create(user=user) # If not using signals
        return user


# --- Profile Serializer ---
class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model.
    Allows user to update their nutritional targets.
    """
    # To display some user info alongside the profile (read-only)
    username = serializers.CharField(source='user.username', read_only=True)
    # Or allow updating via User model
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'user',  # Usually hidden or read-only on input, set automatically
            'username',
            'email',
            'target_calories',
            'target_protein_percent',
            'target_carbs_percent',
            'target_fat_percent',
            # 'dietary_preferences' # If you add this field later
        ]
        # User should be set based on authenticated request
        read_only_fields = ['user']


# --- Ingredient & RecipeIngredient Serializers (for nested display in Recipe) ---
class IngredientSerializer(serializers.ModelSerializer):
    """
    Serializer for Ingredient model (primarily for read-only display within recipes).
    """
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'fdc_id', 'calories_per_100g', 'protein_per_100g',
                  'carbs_per_100g', 'fat_per_100g', 'base_unit', 'usda_food_portions']
        # Consider making most fields read_only if this is just for display
        # read_only_fields = fields # If it's purely for display within a recipe


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """
    Serializer for RecipeIngredient model.
    Shows ingredient details when nested in a Recipe.
    """
    # Nest the full Ingredient details instead of just its ID
    ingredient = IngredientSerializer(read_only=True)
    # Or, if you only want the ingredient name:
    # ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)

    class Meta:
        model = RecipeIngredient
        # 'ingredient_name' if using source
        fields = ['id', 'ingredient', 'quantity', 'unit']
        # If you make RecipeIngredient editable within a Recipe (e.g. for creating new recipes via API):
        # ingredient = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())


# --- Recipe Serializer ---
class RecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for Recipe model.
    Includes calculated nutrition and nested ingredient details.
    """
    # Nest RecipeIngredient details, which in turn nest Ingredient details
    ingredient_details = RecipeIngredientSerializer(many=True, read_only=True)
    # Or use the 'source' argument if your related_name on RecipeIngredient FK is different:
    # ingredients_in_recipe = RecipeIngredientSerializer(source='ingredient_details', many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id',
            'name',
            'description',
            'instructions',
            'meal_type',
            'health_insights',
            'total_calories',  # These are calculated and stored on the model
            'total_protein_g',
            'total_carbs_g',
            'total_fat_g',
            'ingredient_details',  # The nested ingredients
            # 'prep_time_minutes', 'cook_time_minutes', 'servings' # If you add these
        ]
        # For a read-only Recipe list, make all fields read_only
        # read_only_fields = fields

        # If you plan to allow creating/updating recipes via API:
        # You'd need a different approach for 'ingredient_details' to make it writable
        # (e.g., by overriding create/update methods or using a writable nested serializer approach)
        # For now, let's assume recipes are primarily read-only via API or managed via admin.
