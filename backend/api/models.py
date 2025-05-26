from django.db import models
from django.contrib.auth.models import User

class Ingredient(models.Model):
    name = models.CharField(max_length=255, unique=True)
    calories_per_100g = models.FloatField(null=True, blank=True)
    protein_per_100g = models.FloatField(null=True, blank=True)
    carbs_per_100g = models.FloatField(null=True, blank=True)
    fats_per_100g = models.FloatField(null=True, blank=True)
    base_unit = models.CharField(max_length=10, default='g')

    def __str__(self):
        return self.name

class Recipe(models.Model):
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    instructions = models.TextField()
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    health_insights = models.TextField(blank=True, null=True)

    # Calculated fields - will be populated by a method/signal later
    total_calories = models.FloatField(null=True, blank=True)
    total_protein_g = models.FloatField(null=True, blank=True)
    total_carbs_g = models.FloatField(null=True, blank=True)
    total_fat_g = models.FloatField(null=True, blank=True)

    # Ingredients will be linked via the RecipeIngredient model
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient', related_name='recipes')

    # Optional fields
    # prep_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    # cook_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    # servings = models.PositiveIntegerField(default=1, null=True, blank=True)

    def __str__(self):
        return self.name

class RecipeIngredient(models.Model):
    UNIT_CHOICES = [
        ('g', 'Grams'),
        ('ml', 'Milliliters'),
        ('cup', 'Cup'),
        ('tbsp', 'Tablespoon'),
        ('tsp', 'Teaspoon'),
        ('piece', 'Piece'),
        # Add more as needed
    ]
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredient_details')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='used_in_recipes')
    quantity = models.FloatField()
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)

    class Meta:
        unique_together = ('recipe', 'ingredient') # Ensure an ingredient is not listed twice for the same recipe

    def __str__(self):
        return f"{self.quantity} {self.unit} of {self.ingredient.name} for {self.recipe.name}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    target_calories = models.PositiveIntegerField(default=2000)
    target_protein_percent = models.FloatField(default=30.0, help_text="Percentage of total calories")
    target_carbs_percent = models.FloatField(default=40.0, help_text="Percentage of total calories")
    target_fat_percent = models.FloatField(default=30.0, help_text="Percentage of total calories")
    # Optional:
    # dietary_preferences = models.JSONField(null=True, blank=True, help_text="e.g., ['vegetarian', 'no_nuts']")

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Optional: If you want to create UserProfile automatically when a new User is created
# from django.db.models.signals import post_save
# from django.dispatch import receiver

# @receiver(post_save, sender=User)
# def create_or_update_user_profile(sender, instance, created, **kwargs):
#     if created:
#         UserProfile.objects.create(user=instance)
#     instance.profile.save()