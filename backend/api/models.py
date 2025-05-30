from django.contrib.auth.models import User
from django.db import models
import logging
logger = logging.getLogger(__name__)


class Ingredient(models.Model):
    name = models.CharField(max_length=255)
    fdc_id = models.IntegerField(
        unique=True, null=True, blank=True, help_text="FoodData Central ID from USDA")
    calories_per_100g = models.FloatField(null=True, blank=True)
    protein_per_100g = models.FloatField(null=True, blank=True)
    carbs_per_100g = models.FloatField(null=True, blank=True)
    fat_per_100g = models.FloatField(null=True, blank=True)
    base_unit = models.CharField(max_length=10, default='g')
    usda_food_portions = models.JSONField(
        null=True, blank=True, help_text="Raw foodPortions array from USDA API, used for unit conversions")

    def __str__(self):
        return f"{self.name} (FDC ID: {self.fdc_id})" if self.fdc_id else self.name


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
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient', related_name='recipes')

    # Optional fields
    # prep_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    # cook_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    # servings = models.PositiveIntegerField(default=1, null=True, blank=True)

    def __str__(self):
        return self.name

    def get_ingredient_grams(self, recipe_ingredient_instance):
        """
        Converts a RecipeIngredient's quantity and unit to grams,
        prioritizing USDA foodPortions data stored with the Ingredient.
        Checks measureUnit.name, measureUnit.abbreviation, and modifier.
        Returns None if conversion is not possible.
        """
        ingredient_model = recipe_ingredient_instance.ingredient
        quantity = recipe_ingredient_instance.quantity
        unit_from_recipe = recipe_ingredient_instance.unit.lower().strip()

        if quantity <= 0:
            logger.warning(
                f"Non-positive quantity ({quantity}) for {ingredient_model.name} in recipe. Returning 0.0g.")
            return 0.0

        # 1. Direct weight units (most reliable)
        if unit_from_recipe in ['g', 'gram', 'grams']:
            return float(quantity)
        if unit_from_recipe in ['kg', 'kilogram', 'kilograms']:
            return float(quantity) * 1000.0
        # Avoirdupois Ounce (weight)
        if unit_from_recipe in ['oz', 'ounce', 'ounces']:
            return float(quantity) * 28.349523125
        if unit_from_recipe in ['lb', 'pound', 'pounds']:
            return float(quantity) * 453.59237

        # 2. Try to use USDA foodPortions data
        if ingredient_model.usda_food_portions:
            for portion in ingredient_model.usda_food_portions:
                # Extract potential unit strings from the USDA portion data
                usda_measure_unit_name = portion.get(
                    'measureUnit', {}).get('name', '').lower().strip()
                usda_measure_unit_abbr = portion.get('measureUnit', {}).get(
                    'abbreviation', '').lower().strip()

                usda_modifier = portion.get('modifier', '').lower().strip()

                # Build a set of possible unit strings from the USDA portion
                # We'll prioritize modifier if measureUnit is 'undetermined' or generic
                possible_usda_units = set()
                if usda_measure_unit_name and usda_measure_unit_name != 'undetermined':
                    possible_usda_units.add(usda_measure_unit_name)
                    if usda_measure_unit_name + 's' not in possible_usda_units:
                        possible_usda_units.add(usda_measure_unit_name + 's')

                if usda_measure_unit_abbr and usda_measure_unit_abbr != 'undetermined':
                    possible_usda_units.add(usda_measure_unit_abbr)
                    if usda_measure_unit_abbr + 's' not in possible_usda_units:
                        possible_usda_units.add(usda_measure_unit_abbr + 's')

                if usda_modifier:
                    # Try to get the first part of the modifier before a comma, or the whole thing if no comma
                    # Also remove content in parentheses first.
                    modifier_without_parentheses = usda_modifier.split('(')[
                        0].strip()

                    # Split by comma and take the first part as the potential unit
                    potential_unit_from_modifier = modifier_without_parentheses.split(',')[
                        0].strip()

                    if potential_unit_from_modifier:
                        possible_usda_units.add(potential_unit_from_modifier)
                        if potential_unit_from_modifier + 's' not in possible_usda_units:  # simple plural
                            possible_usda_units.add(
                                potential_unit_from_modifier + 's')

                    temp_unit_check = potential_unit_from_modifier

                    # Common aliases for units potentially extracted from modifier
                    if temp_unit_check in ["tbsp", "tbs", "tablespoon"]:
                        possible_usda_units.update(
                            {'tablespoon', 'tbsp', 'tbs'})
                    elif temp_unit_check in ["tsp", "teaspoon"]:
                        possible_usda_units.update({'teaspoon', 'tsp'})
                    elif temp_unit_check in ["cup", "cups"]:
                        possible_usda_units.update({'cup', 'cups'})
                    elif temp_unit_check in ["fl oz", "floz", "fluid ounce"]:
                        possible_usda_units.update(
                            {'fluid ounce', 'fl oz', 'floz'})
                    # Add more specific unit handling here if needed, based on temp_unit_check

                # --- Unit Matching Logic ---
                unit_match = False
                if unit_from_recipe in possible_usda_units:
                    unit_match = True

                # Specific handling for piece-like units, comparing against modifier or ingredient name part
                is_piece_like_unit_from_recipe = unit_from_recipe in [
                    'piece', 'slice', 'each', 'item', 'serving', 'unit', 'container']

                if not unit_match and is_piece_like_unit_from_recipe:
                    is_usda_describing_a_piece = (
                        # Check if the recipe unit matches the unit derived from modifier or measureUnit
                        unit_from_recipe == potential_unit_from_modifier or
                        unit_from_recipe in usda_measure_unit_name or
                        (ingredient_model.name.lower().split(',')[0].strip() in usda_measure_unit_name) or
                        # if potential_unit_from_modifier captured 'slice' etc.
                        (ingredient_model.name.lower().split(',')[
                         0].strip() in potential_unit_from_modifier)
                    )

                    if is_usda_describing_a_piece and portion.get('amount', 0) == 1:
                        unit_match = True

                if unit_match and 'gramWeight' in portion:
                    grams_per_defined_portion_unit = float(
                        portion['gramWeight'])
                    portion_amount_in_definition = float(
                        portion.get('amount', 1.0))
                    if portion_amount_in_definition == 0:
                        portion_amount_in_definition = 1.0

                    grams_per_single_recipe_unit = grams_per_defined_portion_unit / \
                        portion_amount_in_definition

                    converted_grams = float(
                        quantity) * grams_per_single_recipe_unit
                    logger.debug(
                        f"Converted via USDA Portion: {quantity} {unit_from_recipe} of '{ingredient_model.name}' -> {converted_grams:.2f}g "
                        f"(using USDA portion: measureUnit='{usda_measure_unit_name}', modifier='{usda_modifier}', "
                        f"matched_units='{possible_usda_units}', gramWeight: {grams_per_defined_portion_unit}, portionAmount: {portion_amount_in_definition})"
                    )
                    return converted_grams

            # If loop finishes, no suitable USDA portion was found
            logger.info(
                f"No suitable USDA foodPortion found for unit '{unit_from_recipe}' of ingredient '{ingredient_model.name}'. Trying fallbacks.")

        # 3. Fallback for ml (if not covered by USDA portions which might have "fl oz" or "cup (8 fl oz)")
        if unit_from_recipe in ['ml', 'milliliter', 'milliliters']:
            density = 1.0  # g/ml for water-like substances
            if "oil" in ingredient_model.name.lower():
                density = 0.92
                logger.info(
                    f"Using oil density ({density} g/ml) for '{ingredient_model.name}' for ml fallback conversion.")
            else:
                logger.info(
                    f"Using water density (1.0 g/ml) for '{ingredient_model.name}' for ml fallback conversion.")
            return float(quantity) * density

        logger.error(
            f"FAILED CONVERSION: Cannot convert unit '{unit_from_recipe}' to grams for ingredient '{ingredient_model.name}' (FDC ID: {ingredient_model.fdc_id}).")
        return None

    def calculate_nutrition(self, save_to_instance=True):
        """
        Calculates the total nutritional information for this recipe.
        If save_to_instance is True, it updates the recipe instance's fields.
        Returns a dictionary with total nutrition, or None if critical errors occur.
        """
        total_nutrition = {
            'calories': 0.0,
            'protein': 0.0,
            'fat': 0.0,
            'carbs': 0.0,
        }
        calculation_successful = True  # Assume success initially

        # 'ingredient_details' is the related_name from RecipeIngredient.recipe FK
        for ri in self.ingredient_details.all():
            ingredient_model = ri.ingredient

            quantity_in_grams = self.get_ingredient_grams(ri)

            if quantity_in_grams is None:
                logger.error(
                    f"Nutrition calc error: Could not determine gram weight for '{ri.quantity} {ri.unit} of {ingredient_model.name}' in Recipe '{self.name}'. Omitting from totals.")
                calculation_successful = False  # Mark that at least one ingredient failed
                continue  # Skip this ingredient

            # Ensure ingredient has nutritional data
            if None in [ingredient_model.calories_per_100g, ingredient_model.protein_per_100g,
                        ingredient_model.fat_per_100g, ingredient_model.carbs_per_100g]:
                logger.warning(f"Nutrition calc warning: Ingredient '{ingredient_model.name}' (FDC ID: {ingredient_model.fdc_id}) "
                               f"is missing one or more core nutritional values (per 100g). Its contribution will be incomplete.")

            # Add to totals, checking for None to avoid TypeError
            total_nutrition['calories'] += (
                (ingredient_model.calories_per_100g or 0.0) / 100.0) * quantity_in_grams
            total_nutrition['protein'] += (
                (ingredient_model.protein_per_100g or 0.0) / 100.0) * quantity_in_grams
            total_nutrition['fat'] += (
                (ingredient_model.fat_per_100g or 0.0) / 100.0) * quantity_in_grams
            total_nutrition['carbs'] += (
                (ingredient_model.carbs_per_100g or 0.0) / 100.0) * quantity_in_grams

        if not calculation_successful:
            logger.warning(
                f"Nutritional calculation for Recipe '{self.name}' is INCOMPLETE due to one or more ingredient conversion failures.")

        if save_to_instance:
            self.total_calories = round(total_nutrition['calories'], 2)
            self.total_protein_g = round(total_nutrition['protein'], 2)
            self.total_fat_g = round(total_nutrition['fat'], 2)
            self.total_carbs_g = round(total_nutrition['carbs'], 2)
            # Only save if all conversions were successful or if partial results are acceptable
            # if calculation_successful:
            self.save(update_fields=[
                      'total_calories', 'total_protein_g', 'total_fat_g', 'total_carbs_g'])
            logger.info(
                f"Nutrition calculated and saved for Recipe: {self.name} - Calories: {self.total_calories}")
            # else:
            #    logger.error(f"Nutrition not saved for Recipe: {self.name} due to calculation incompleteness.")

        # Or always return total_nutrition dict
        return total_nutrition if calculation_successful else None


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
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='ingredient_details')
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name='used_in_recipes')
    quantity = models.FloatField()
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)

    class Meta:
        # Ensure an ingredient is not listed twice for the same recipe
        unique_together = ('recipe', 'ingredient')

    def __str__(self):
        return f"{self.quantity} {self.unit} of {self.ingredient.name} for {self.recipe.name}"


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    target_calories = models.PositiveIntegerField(default=2000)
    target_protein_percent = models.FloatField(
        default=30.0, help_text="Percentage of total calories")
    target_carbs_percent = models.FloatField(
        default=40.0, help_text="Percentage of total calories")
    target_fat_percent = models.FloatField(
        default=30.0, help_text="Percentage of total calories")
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
