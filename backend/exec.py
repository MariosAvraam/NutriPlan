
from api.models import Recipe, Ingredient, RecipeIngredient
import logging

# Optional: Configure logging to see output in the shell clearly
# This will show INFO and higher level messages from your 'api.models' logger
# Get the logger you defined in models.py
logger = logging.getLogger('api.models')
# Set to DEBUG to see more detailed logs from get_ingredient_grams
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.hasHandlers():  # Avoid adding multiple handlers if you re-run this block
    logger.addHandler(handler)


def get_ingredient(name_or_fdc_id):
    try:
        if isinstance(name_or_fdc_id, int) or (isinstance(name_or_fdc_id, str) and name_or_fdc_id.isdigit()):
            return Ingredient.objects.get(fdc_id=int(name_or_fdc_id))
        else:
            # Be careful with name matching, it needs to be exact
            return Ingredient.objects.get(name__iexact=name_or_fdc_id)
    except Ingredient.DoesNotExist:
        print(
            f"ERROR: Ingredient '{name_or_fdc_id}' not found in the database. Make sure it's populated.")
        return None
    except Ingredient.MultipleObjectsReturned:
        print(
            f"ERROR: Multiple ingredients found for '{name_or_fdc_id}'. Use a more specific identifier (like FDC ID).")
        return None


# Fetch ingredients we'll use:
# Replace with FDC IDs or exact names of ingredients you've populated
flour = get_ingredient(169761)  # Flour, all-purpose
sugar = get_ingredient(169655)  # Sugar, granulated
olive_oil = get_ingredient(171413)  # Olive oil
# Apple, raw, with skin (or similar FDC ID from your pre_vetted_list)
apple = get_ingredient(171688)
# Add an ingredient that might cause conversion issues
# e.g., one you manually add without USDA portions, or one with a tricky unit
# For now, let's assume 'unknown_item' is one such example we'll create or expect to fail
# This will likely print an error unless you add it
unknown_item = get_ingredient("A completely made up item")

# Verify they were fetched
print(f"Flour: {flour}")
print(f"Sugar: {sugar}")
print(f"Olive Oil: {olive_oil}")
print(f"Apple: {apple}")

if flour and sugar:
    # Create the Recipe
    recipe1, created1 = Recipe.objects.get_or_create(
        name="Test Pancakes",
        defaults={
            'instructions': "Mix and cook.",
            'meal_type': 'breakfast'
        }
    )
    if not created1:  # If it exists, clear old ingredients for a clean test
        recipe1.ingredient_details.all().delete()
        recipe1.total_calories = None  # Reset calculated fields
        recipe1.total_protein_g = None
        recipe1.total_carbs_g = None
        recipe1.total_fat_g = None
        recipe1.save()
    print(f"\n--- Testing Recipe 1: Test Pancakes (All Successful) ---")

    # Add RecipeIngredients
    ri1_flour = RecipeIngredient.objects.create(
        recipe=recipe1, ingredient=flour, quantity=2, unit='cup')
    ri1_sugar = RecipeIngredient.objects.create(
        recipe=recipe1, ingredient=sugar, quantity=50, unit='g')

    # Test get_ingredient_grams individually (optional, but good for isolating)
    print(f"Flour (2 cup) in grams: {recipe1.get_ingredient_grams(ri1_flour)}")
    print(f"Sugar (50 g) in grams: {recipe1.get_ingredient_grams(ri1_sugar)}")

    # Test calculate_nutrition
    print("Calculating nutrition for Test Pancakes...")
    calculated_nutrition1 = recipe1.calculate_nutrition(save_to_instance=True)
    print(f"Calculated Nutrition (dict): {calculated_nutrition1}")

    # Verify database
    recipe1.refresh_from_db()  # Get the latest data from DB
    print(
        f"Recipe 1 in DB - Calories: {recipe1.total_calories}, Protein: {recipe1.total_protein_g}, Carbs: {recipe1.total_carbs_g}, Fat: {recipe1.total_fat_g}")
else:
    print("Skipping Scenario 1 due to missing base ingredients.")

if olive_oil and apple:
    recipe2, created2 = Recipe.objects.get_or_create(
        name="Test Apple Salad Dressing",
        defaults={'instructions': "Mix well.", 'meal_type': 'lunch'}
    )
    if not created2:
        recipe2.ingredient_details.all().delete()
        recipe2.total_calories = None
        recipe2.total_protein_g = None
        recipe2.total_carbs_g = None
        recipe2.total_fat_g = None
        recipe2.save()
    print(f"\n--- Testing Recipe 2: Test Apple Salad Dressing (ML & Piece) ---")

    ri2_oil = RecipeIngredient.objects.create(
        recipe=recipe2, ingredient=olive_oil, quantity=30, unit='ml')
    ri2_apple = RecipeIngredient.objects.create(
        recipe=recipe2, ingredient=apple, quantity=1, unit='piece')

    # Expect ~27.6g
    print(
        f"Olive Oil (30 ml) in grams: {recipe2.get_ingredient_grams(ri2_oil)}")
    # Expect ~182g if your apple is like Ingredient 4
    print(
        f"Apple (1 piece) in grams: {recipe2.get_ingredient_grams(ri2_apple)}")

    print("Calculating nutrition for Test Apple Salad Dressing...")
    calculated_nutrition2 = recipe2.calculate_nutrition(save_to_instance=True)
    print(f"Calculated Nutrition (dict): {calculated_nutrition2}")

    recipe2.refresh_from_db()
    print(
        f"Recipe 2 in DB - Calories: {recipe2.total_calories}, Protein: {recipe2.total_protein_g}")
else:
    print("Skipping Scenario 2 due to missing Olive Oil or Apple.")


if flour and sugar:  # Reusing sugar for this, but with a bad unit
    recipe3, created3 = Recipe.objects.get_or_create(
        name="Test Mystery Mix",
        defaults={'instructions': "Good luck.", 'meal_type': 'snack'}
    )
    if not created3:
        recipe3.ingredient_details.all().delete()
        recipe3.total_calories = None
        recipe3.total_protein_g = None
        recipe3.total_carbs_g = None
        recipe3.total_fat_g = None
        recipe3.save()
    print(f"\n--- Testing Recipe 3: Test Mystery Mix (Conversion Failure) ---")

    ri3_flour = RecipeIngredient.objects.create(
        recipe=recipe3, ingredient=flour, quantity=100, unit='g')
    # Using sugar but with a unit ('fling') that will definitely fail conversion
    ri3_bad_unit = RecipeIngredient.objects.create(
        recipe=recipe3, ingredient=sugar, quantity=1, unit='fling')

    print(f"Flour (100g) in grams: {recipe3.get_ingredient_grams(ri3_flour)}")
    # Expect None
    print(
        f"Sugar (1 fling) in grams: {recipe3.get_ingredient_grams(ri3_bad_unit)}")

    print("Calculating nutrition for Test Mystery Mix...")
    calculated_nutrition3 = recipe3.calculate_nutrition(save_to_instance=True)
    # Note if it's None or partial
    print(f"Calculated Nutrition (dict): {calculated_nutrition3}")

    recipe3.refresh_from_db()
    print(
        f"Recipe 3 in DB - Calories: {recipe3.total_calories}, Protein: {recipe3.total_protein_g}")
    # Expect totals to only reflect flour if sugar conversion failed.
    # Check if the `calculation_successful` flag in the returned dict is False (or if dict is None, depending on exact return logic)
    if calculated_nutrition3:  # Check if dict was returned
        # You might want to inspect a flag for success if your method adds one to the dict.
        # For now, we check if the logger warned about incompleteness.
        pass
else:
    print("Skipping Scenario 3 due to missing Flour or Sugar.")

# First, create or ensure such an ingredient exists
# Make sure this one has NO usda_food_portions or very simple ones if needed for unit conversion
bland_ingredient, created_bland = Ingredient.objects.get_or_create(
    name="Nutritionally Incomplete Test Food",
    defaults={
        'fdc_id': 9999999,  # Make sure this FDC ID is unique and won't conflict
        'calories_per_100g': None,  # INTENTIONALLY MISSING
        'protein_per_100g': 10.0,  # Has some other data
        'carbs_per_100g': 5.0,
        'fat_per_100g': 1.0,
        'usda_food_portions': []  # No USDA portions to keep it simple
    }
)
if not created_bland:  # If it existed, ensure calories are None
    bland_ingredient.calories_per_100g = None
    bland_ingredient.save()

if bland_ingredient:
    recipe4, created4 = Recipe.objects.get_or_create(
        name="Test Bland Meal",
        defaults={'instructions': "Eat if you must.", 'meal_type': 'snack'}
    )
    if not created4:
        recipe4.ingredient_details.all().delete()
        recipe4.total_calories = None
        recipe4.total_protein_g = None
        recipe4.total_carbs_g = None
        recipe4.total_fat_g = None
        recipe4.save()
    print(f"\n--- Testing Recipe 4: Test Bland Meal (Ingredient Missing Nutrition) ---")

    ri4_bland = RecipeIngredient.objects.create(
        recipe=recipe4, ingredient=bland_ingredient, quantity=100, unit='g')

    print(
        f"Bland Ingredient (100g) in grams: {recipe4.get_ingredient_grams(ri4_bland)}")

    print("Calculating nutrition for Test Bland Meal...")
    calculated_nutrition4 = recipe4.calculate_nutrition(save_to_instance=True)
    print(f"Calculated Nutrition (dict): {calculated_nutrition4}")

    recipe4.refresh_from_db()
    print(
        f"Recipe 4 in DB - Calories: {recipe4.total_calories}, Protein: {recipe4.total_protein_g}")
    # Expect Calories to be 0 or very low, but Protein should be calculated.
else:
    print("Skipping Scenario 4, bland_ingredient could not be setup.")

# Recipe.objects.filter(name__startswith="Test ").delete()
# Ingredient.objects.filter(name="Nutritionally Incomplete Test Food").delete()
