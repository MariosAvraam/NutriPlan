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

    # Calculated fields
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

    # This function may need to be enhanced to more accurately convert non-gram portions into grams
    def get_ingredient_grams(self, recipe_ingredient_instance):
        """
        Converts a RecipeIngredient's quantity and unit to grams,
        prioritizing USDA foodPortions data stored with the Ingredient.
        Checks measureUnit.name, measureUnit.abbreviation, and modifier.
        Returns None if conversion is not possible.
        """
        logger.debug(
            f"get_ingredient_grams called for RI ID: {recipe_ingredient_instance.id}, "
            f"Ingredient: '{recipe_ingredient_instance.ingredient.name}', "
            f"Quantity: {recipe_ingredient_instance.quantity}, Unit: '{recipe_ingredient_instance.unit}'"
        )

        ingredient_model = recipe_ingredient_instance.ingredient
        quantity = recipe_ingredient_instance.quantity
        unit_from_recipe = recipe_ingredient_instance.unit.lower().strip()

        logger.debug(
            f"Processing: Ingredient='{ingredient_model.name}' (FDC ID: {ingredient_model.fdc_id}), "
            f"Recipe Quantity='{quantity}', Recipe Unit='{unit_from_recipe}'"
        )

        if quantity <= 0:
            logger.warning(
                f"Non-positive quantity ({quantity}) for {ingredient_model.name} in recipe. Returning 0.0g.")
            return 0.0

        # 1. Direct weight units (most reliable)
        logger.debug(
            f"Attempting direct weight unit conversion for '{unit_from_recipe}'.")
        if unit_from_recipe in ['g', 'gram', 'grams']:
            result = float(quantity)
            logger.info(
                f"Direct conversion: '{unit_from_recipe}' to grams. {quantity} {unit_from_recipe} = {result}g for '{ingredient_model.name}'."
            )
            return result
        if unit_from_recipe in ['kg', 'kilogram', 'kilograms']:
            result = float(quantity) * 1000.0
            logger.info(
                f"Direct conversion: '{unit_from_recipe}' to grams. {quantity} {unit_from_recipe} = {result}g for '{ingredient_model.name}'."
            )
            return result
        # Avoirdupois Ounce (weight)
        if unit_from_recipe in ['oz', 'ounce', 'ounces']:
            result = float(quantity) * 28.349523125
            logger.info(
                f"Direct conversion: '{unit_from_recipe}' (oz) to grams. {quantity} {unit_from_recipe} = {result}g for '{ingredient_model.name}'."
            )
            return result
        if unit_from_recipe in ['lb', 'pound', 'pounds']:
            result = float(quantity) * 453.59237
            logger.info(
                f"Direct conversion: '{unit_from_recipe}' (lb) to grams. {quantity} {unit_from_recipe} = {result}g for '{ingredient_model.name}'."
            )
            return result
        logger.debug("No direct weight unit match.")

        # 2. Try to use USDA foodPortions data
        if ingredient_model.usda_food_portions:
            logger.debug(
                f"Attempting USDA foodPortions conversion for '{ingredient_model.name}'. Found {len(ingredient_model.usda_food_portions)} portions."
            )
            for i, portion in enumerate(ingredient_model.usda_food_portions):
                logger.debug(f"Evaluating USDA Portion #{i+1}: {portion}")
                # Extract potential unit strings from the USDA portion data
                usda_measure_unit_name = portion.get(
                    'measureUnit', {}).get('name', '').lower().strip()
                usda_measure_unit_abbr = portion.get('measureUnit', {}).get(
                    'abbreviation', '').lower().strip()
                usda_modifier = portion.get('modifier', '').lower().strip()
                logger.debug(
                    f"USDA Portion data: measureUnit.name='{usda_measure_unit_name}', "
                    f"measureUnit.abbr='{usda_measure_unit_abbr}', modifier='{usda_modifier}'"
                )

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

                potential_unit_from_modifier = ""  # Initialize
                if usda_modifier:
                    modifier_without_parentheses = usda_modifier.split('(')[
                        0].strip()
                    potential_unit_from_modifier = modifier_without_parentheses.split(',')[
                        0].strip()
                    logger.debug(
                        f"Extracted potential unit from modifier '{usda_modifier}': '{potential_unit_from_modifier}'")

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
                logger.debug(
                    f"Built possible_usda_units: {possible_usda_units} for comparison with recipe unit '{unit_from_recipe}'")

                # --- Unit Matching Logic ---
                unit_match = False
                if unit_from_recipe in possible_usda_units:
                    unit_match = True
                    logger.debug(
                        f"Direct match found: recipe unit '{unit_from_recipe}' in possible_usda_units.")

                is_piece_like_unit_from_recipe = unit_from_recipe in [
                    'piece', 'slice', 'each', 'item', 'serving', 'unit', 'container']
                logger.debug(
                    f"Recipe unit '{unit_from_recipe}' is piece-like: {is_piece_like_unit_from_recipe}")

                if not unit_match and is_piece_like_unit_from_recipe:
                    logger.debug("Attempting piece-like unit matching logic.")
                    is_usda_describing_a_piece = (
                        unit_from_recipe == potential_unit_from_modifier or
                        unit_from_recipe in usda_measure_unit_name or
                        (ingredient_model.name.lower().split(',')[0].strip() in usda_measure_unit_name) or
                        (ingredient_model.name.lower().split(',')[
                         0].strip() in potential_unit_from_modifier)
                    )
                    logger.debug(f"Is USDA portion describing a piece-like unit for '{unit_from_recipe}'? {is_usda_describing_a_piece}. "
                                 f"Portion amount: {portion.get('amount', 0)}")

                    if is_usda_describing_a_piece and portion.get('amount', 0) == 1:
                        unit_match = True
                        logger.debug(
                            "Piece-like unit match confirmed via USDA portion attributes and amount=1.")

                if unit_match and 'gramWeight' in portion:
                    logger.info(
                        f"Unit match SUCCESS for '{unit_from_recipe}' with USDA portion. GramWeight available.")
                    grams_per_defined_portion_unit = float(
                        portion['gramWeight'])
                    portion_amount_in_definition = float(
                        portion.get('amount', 1.0))
                    if portion_amount_in_definition == 0:
                        logger.warning(
                            f"USDA Portion (modifier='{usda_modifier}') has amount 0, defaulting to 1.0 to avoid division by zero.")
                        portion_amount_in_definition = 1.0

                    grams_per_single_recipe_unit = grams_per_defined_portion_unit / \
                        portion_amount_in_definition

                    converted_grams = float(
                        quantity) * grams_per_single_recipe_unit
                    logger.debug(
                        f"Converted via USDA Portion: {quantity} {unit_from_recipe} of '{ingredient_model.name}' -> {converted_grams:.2f}g "
                        f"(using USDA portion: measureUnit='{usda_measure_unit_name}', modifier='{usda_modifier}', "
                        f"matched_units='{possible_usda_units}', gramWeight: {grams_per_defined_portion_unit}, "
                        f"portionAmount: {portion_amount_in_definition}, grams_per_single_unit: {grams_per_single_recipe_unit})"
                    )
                    return converted_grams
                elif unit_match:
                    logger.debug(
                        f"Unit '{unit_from_recipe}' matched USDA portion, but 'gramWeight' is missing in portion data: {portion}")
                else:
                    logger.debug(
                        f"No unit match for recipe unit '{unit_from_recipe}' with this USDA portion.")

            # If loop finishes, no suitable USDA portion was found
            logger.info(
                f"No suitable USDA foodPortion found after checking all portions for unit '{unit_from_recipe}' of ingredient '{ingredient_model.name}'. Trying fallbacks."
            )
        else:
            logger.debug(
                f"No USDA foodPortions data available for ingredient '{ingredient_model.name}'. Trying fallbacks.")

        # 3. Fallback for ml (if not covered by USDA portions which might have "fl oz" or "cup (8 fl oz)")
        logger.debug(
            f"Attempting fallback for ml-based units for '{unit_from_recipe}'.")
        if unit_from_recipe in ['ml', 'milliliter', 'milliliters']:
            density = 1.0  # g/ml for water-like substances
            if "oil" in ingredient_model.name.lower():
                density = 0.92
                logger.info(
                    f"Using oil density ({density} g/ml) for '{ingredient_model.name}' for ml fallback conversion.")
            # Add other common densities if needed, e.g., milk, flour
            # elif "milk" in ingredient_model.name.lower():
            #     density = 1.03
            #     logger.info(f"Using milk density ({density} g/ml) ...")
            else:
                logger.info(
                    f"Using water density (1.0 g/ml) for '{ingredient_model.name}' for ml fallback conversion.")
            result = float(quantity) * density
            logger.info(
                f"Fallback ML conversion: {quantity} {unit_from_recipe} of '{ingredient_model.name}' -> {result:.2f}g (using density {density} g/ml)."
            )
            return result
        logger.debug("No ml-based fallback match.")

        logger.error(
            f"FAILED CONVERSION: Cannot convert unit '{unit_from_recipe}' to grams for ingredient '{ingredient_model.name}' (FDC ID: {ingredient_model.fdc_id}). Quantity: {quantity}."
        )
        return None

    def calculate_nutrition(self, save_to_instance=True):
        """
        Calculates the total nutritional information for this recipe.
        If save_to_instance is True, it updates the recipe instance's fields.
        Returns a dictionary with total nutrition, or None if critical errors occur.
        """
        logger.info(
            f"Starting nutrition calculation for Recipe '{self.name}'. Save to instance: {save_to_instance}."
        )
        total_nutrition = {
            'calories': 0.0,
            'protein': 0.0,
            'fat': 0.0,
            'carbs': 0.0,
        }
        logger.debug(f"Initial total_nutrition: {total_nutrition}")
        calculation_successful = True  # Assume success initially
        processed_ingredients_count = 0

        # 'ingredient_details' is the related_name from RecipeIngredient.recipe FK
        recipe_ingredients = self.ingredient_details.all()
        logger.debug(
            f"Recipe '{self.name}' has {len(recipe_ingredients)} ingredient instance(s).")

        for i, ri in enumerate(recipe_ingredients):
            ingredient_model = ri.ingredient
            logger.info(
                f"Processing ingredient #{i+1}: '{ingredient_model.name}' (ID: {ingredient_model.id}), "
                f"Quantity: {ri.quantity}, Unit: '{ri.unit}'"
            )

            quantity_in_grams = self.get_ingredient_grams(
                ri)  # This will generate its own logs

            if quantity_in_grams is None:
                logger.error(
                    f"Nutrition calc error for Recipe '{self.name}': Could not determine gram weight for "
                    f"'{ri.quantity} {ri.unit} of {ingredient_model.name}'. Omitting from totals."
                )
                calculation_successful = False  # Mark that at least one ingredient failed
                continue  # Skip this ingredient

            if quantity_in_grams == 0.0:  # Could be due to non-positive quantity or explicit 0g conversion
                logger.info(
                    f"Ingredient '{ingredient_model.name}' has 0.0g effective quantity. Skipping its nutritional contribution."
                )
                processed_ingredients_count += 1
                continue

            logger.debug(
                f"Successfully converted '{ingredient_model.name}' to {quantity_in_grams:.2f}g."
            )

            # Ensure ingredient has nutritional data
            if None in [ingredient_model.calories_per_100g, ingredient_model.protein_per_100g,
                        ingredient_model.fat_per_100g, ingredient_model.carbs_per_100g]:
                logger.warning(f"Nutrition calc warning for Recipe '{self.name}': Ingredient '{ingredient_model.name}' (FDC ID: {ingredient_model.fdc_id}) "
                               f"is missing one or more core nutritional values (per 100g). Its contribution will be incomplete or zero for those nutrients.")

            # Calculate contribution for this ingredient
            calories_contrib = (
                (ingredient_model.calories_per_100g or 0.0) / 100.0) * quantity_in_grams
            protein_contrib = (
                (ingredient_model.protein_per_100g or 0.0) / 100.0) * quantity_in_grams
            fat_contrib = (
                (ingredient_model.fat_per_100g or 0.0) / 100.0) * quantity_in_grams
            carbs_contrib = (
                (ingredient_model.carbs_per_100g or 0.0) / 100.0) * quantity_in_grams

            logger.debug(
                f"Nutrient contribution from {quantity_in_grams:.2f}g of '{ingredient_model.name}': "
                f"Calories={calories_contrib:.2f}, Protein={protein_contrib:.2f}g, "
                f"Fat={fat_contrib:.2f}g, Carbs={carbs_contrib:.2f}g"
            )
            logger.debug(
                f" (Raw per 100g: Cal={ingredient_model.calories_per_100g}, Prot={ingredient_model.protein_per_100g}, "
                f"Fat={ingredient_model.fat_per_100g}, Carb={ingredient_model.carbs_per_100g})"
            )

            # Add to totals
            total_nutrition['calories'] += calories_contrib
            total_nutrition['protein'] += protein_contrib
            total_nutrition['fat'] += fat_contrib
            total_nutrition['carbs'] += carbs_contrib
            processed_ingredients_count += 1

            logger.debug(
                f"Cumulative total_nutrition after '{ingredient_model.name}': {total_nutrition}")

        logger.info(
            f"Finished processing {processed_ingredients_count}/{len(recipe_ingredients)} ingredients for Recipe '{self.name}'."
        )

        if not calculation_successful:
            logger.warning(
                f"Nutritional calculation for Recipe '{self.name}' is INCOMPLETE due to one or more ingredient conversion failures. "
                f"Final (partial) totals: {total_nutrition}"
            )
        else:
            logger.info(
                f"Nutritional calculation for Recipe '{self.name}' completed. Final totals: {total_nutrition}"
            )

        if save_to_instance:
            logger.debug(
                f"Attempting to save calculated nutrition to instance for Recipe '{self.name}'.")
            self.total_calories = round(total_nutrition['calories'], 2)
            self.total_protein_g = round(total_nutrition['protein'], 2)
            self.total_fat_g = round(total_nutrition['fat'], 2)
            self.total_carbs_g = round(total_nutrition['carbs'], 2)

            update_fields_list = [
                'total_calories', 'total_protein_g', 'total_fat_g', 'total_carbs_g']
            # Assuming self.save exists
            self.save(update_fields=update_fields_list)
            logger.info(
                f"Nutrition calculated and (simulated) saved for Recipe: {self.name} - "
                f"Calories: {self.total_calories}, Protein: {self.total_protein_g}g, "
                f"Fat: {self.total_fat_g}g, Carbs: {self.total_carbs_g}g. Updated fields: {update_fields_list}"
            )
        else:
            logger.info(
                f"Skipping save to instance for Recipe '{self.name}' as per 'save_to_instance=False'.")

        if calculation_successful:
            logger.debug(
                f"calculate_nutrition returning successful totals for Recipe '{self.name}'.")
            return total_nutrition
        else:
            logger.warning(
                f"calculate_nutrition returning None for Recipe '{self.name}' due to incomplete calculation.")
            return None


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
