import random
from .models import Recipe
import logging

logger = logging.getLogger(__name__)


# --- Constants for Algorithm Behavior ---
NUM_ATTEMPTS = 50
MEAL_SLOTS_ORDER = ['breakfast', 'lunch',
                    'dinner', 'snack']  # Define order and types
# Heuristic allocation percentages for initial meal target estimation
MEAL_ALLOCATION_PERCENTAGES = {
    'breakfast': 0.25,
    'lunch': 0.35,
    'dinner': 0.30,
    'snack': 0.10,  # If you have one snack
}
# Acceptable deviation for a "good enough" plan
CALORIE_DEVIATION_PERCENT = 0.15  # +/- 10%
MACRO_DEVIATION_GRAMS = 15  # +/- 10g for protein, car


def calculate_recipe_fitness_score(recipe_nutrition, meal_slot_targets):
    # recipe_nutrition: {'calories': X, 'protein': Y, ...}
    # meal_slot_targets: {'calories': A, 'protein': B, ...}

    score = 0
    # Weights can be adjusted if matching one nutrient is more important

    score += abs(recipe_nutrition.get('calories', 0) -
                 meal_slot_targets.get('calories', 0)) * 1.0  # Weight for calories
    # Weight for protein (protein is 4kcal/g)
    score += abs(recipe_nutrition.get('protein', 0) -
                 meal_slot_targets.get('protein', 0)) * 4.0
    score += abs(recipe_nutrition.get('carbs', 0) -
                 meal_slot_targets.get('carbs', 0)) * 4.0     # Weight for carbs
    score += abs(recipe_nutrition.get('fat', 0) -
                 meal_slot_targets.get('fat', 0)) * 9.0       # Weight for fat
    return score


def calculate_daily_plan_fitness_score(plan_totals, user_daily_targets):
    # Similar to recipe fitness but for the whole day's plan vs user's total daily targets
    score = 0
    score += abs(plan_totals.get('calories', 0) -
                 user_daily_targets.get('calories', 0)) * 1.0
    score += abs(plan_totals.get('protein', 0) -
                 user_daily_targets.get('protein_g', 0)) * 1.0  # Use grams directly
    score += abs(plan_totals.get('carbs', 0) -
                 user_daily_targets.get('carbs_g', 0)) * 1.0
    score += abs(plan_totals.get('fat', 0) -
                 user_daily_targets.get('fat_g', 0)) * 1.0
    return score


def generate_daily_meal_plan_v1(user_profile):
    target_calories = user_profile.target_calories
    # Convert percentages to grams
    target_protein_g = (
        target_calories * user_profile.target_protein_percent / 100) / 4
    target_carbs_g = (target_calories *
                      user_profile.target_carbs_percent / 100) / 4
    target_fat_g = (target_calories *
                    user_profile.target_fat_percent / 100) / 9

    user_daily_targets = {
        'calories': target_calories,
        'protein_g': target_protein_g,
        'carbs_g': target_carbs_g,
        'fat_g': target_fat_g,
    }

    logger.info(
        f"Attempting to generate meal plan for targets: {user_daily_targets}")

    # Fetch all relevant recipes once
    all_recipes = list(Recipe.objects.filter(
        total_calories__isnull=False  # Ensure recipes have calculated nutrition
    ))

    if not all_recipes:
        logger.warning(
            "No recipes with calculated nutrition found in the database.")
        return None  # Or raise an error

    recipes_by_meal_type = {
        meal_type: [r for r in all_recipes if r.meal_type == meal_type]
        for meal_type in MEAL_SLOTS_ORDER
    }

    best_plan = None
    best_plan_score = float('inf')
    best_plan_totals = {}

    for attempt in range(NUM_ATTEMPTS):
        # Stores Recipe objects: {'breakfast': recipe_obj, ...}
        current_day_plan_recipes = {}
        current_day_totals = {'calories': 0,
                              'protein': 0, 'carbs': 0, 'fat': 0}

        # Make a copy of targets for this attempt to modify
        remaining_targets_for_attempt = user_daily_targets.copy()

        possible_attempt = True
        for meal_slot in MEAL_SLOTS_ORDER:
            if not recipes_by_meal_type.get(meal_slot):
                logger.debug(
                    f"Attempt {attempt+1}: No recipes for meal slot {meal_slot}. Skipping slot.")
                # Mark slot as empty
                current_day_plan_recipes[meal_slot] = None
                continue

            # Simplified target for this meal slot based on initial allocation
            # More advanced: allocate based on remaining needs and remaining slots
            meal_slot_target_calories = user_daily_targets['calories'] * \
                MEAL_ALLOCATION_PERCENTAGES.get(meal_slot, 0.1)
            meal_slot_target_protein = user_daily_targets['protein_g'] * \
                MEAL_ALLOCATION_PERCENTAGES.get(meal_slot, 0.1)
            meal_slot_target_carbs = user_daily_targets['carbs_g'] * \
                MEAL_ALLOCATION_PERCENTAGES.get(meal_slot, 0.1)
            meal_slot_target_fat = user_daily_targets['fat_g'] * \
                MEAL_ALLOCATION_PERCENTAGES.get(meal_slot, 0.1)

            meal_slot_ideal_targets = {
                'calories': meal_slot_target_calories,
                'protein': meal_slot_target_protein,
                'carbs': meal_slot_target_carbs,
                'fat': meal_slot_target_fat,
            }

            candidate_recipes = []
            for recipe in recipes_by_meal_type[meal_slot]:
                recipe_nutrition = {
                    'calories': recipe.total_calories or 0,
                    'protein': recipe.total_protein_g or 0,
                    'carbs': recipe.total_carbs_g or 0,
                    'fat': recipe.total_fat_g or 0,
                }
                # Simple check: don't pick a recipe that alone exceeds remaining daily calories by too much
                # This constraint needs careful tuning.
                if recipe_nutrition['calories'] > remaining_targets_for_attempt['calories'] * 1.5 and \
                   sum(1 for r in current_day_plan_recipes.values() if r is not None) < len(MEAL_SLOTS_ORDER) - 1:  # if not the last meal
                    continue  # Too big for this slot given what's remaining

                score = calculate_recipe_fitness_score(
                    recipe_nutrition, meal_slot_ideal_targets)
                candidate_recipes.append(
                    {'recipe': recipe, 'score': score, 'nutrition': recipe_nutrition})

            if not candidate_recipes:
                logger.debug(
                    f"Attempt {attempt+1}: No suitable candidate recipes found for {meal_slot}.")
                possible_attempt = False
                break  # This attempt failed to fill a slot

            candidate_recipes.sort(key=lambda x: x['score'])

            # Selection strategy: pick best, or one of top few randomly
            # For now, let's pick the best one that fits reasonably
            selected_candidate = None
            for cand in candidate_recipes[:5]:  # Check top 5
                # A more refined check against remaining_targets_for_attempt could go here
                selected_candidate = cand
                break

            if selected_candidate:
                current_day_plan_recipes[meal_slot] = selected_candidate['recipe']
                for key in current_day_totals:
                    current_day_totals[key] += selected_candidate['nutrition'][key]
                # Update remaining targets (simplified: just subtract from total for fitness check)
                # A more complex remaining_targets_for_attempt would be continuously updated.
            else:
                logger.debug(
                    f"Attempt {attempt+1}: Could not select a recipe for {meal_slot} from candidates.")
                possible_attempt = False
                break

        # Ensure main meals are filled
        if possible_attempt and all(current_day_plan_recipes.get(slot) for slot in ['breakfast', 'lunch', 'dinner']):
            daily_score = calculate_daily_plan_fitness_score(
                current_day_totals, user_daily_targets)
            logger.debug(
                f"Attempt {attempt+1}: Plan generated with score {daily_score:.2f}. Totals: C:{current_day_totals['calories']:.0f}, P:{current_day_totals['protein']:.0f}, C:{current_day_totals['carbs']:.0f}, F:{current_day_totals['fat']:.0f}")

            if daily_score < best_plan_score:
                # Check if it's within acceptable deviation
                cal_dev = abs(
                    current_day_totals['calories'] - user_daily_targets['calories']) / user_daily_targets['calories']
                pro_dev = abs(
                    current_day_totals['protein'] - user_daily_targets['protein_g'])
                # ... check other macros ...

                # For V1, let's just take the best score. Deviation checks can be added.
                best_plan_score = daily_score
                best_plan = current_day_plan_recipes
                best_plan_totals = current_day_totals
        else:
            logger.debug(
                f"Attempt {attempt+1}: Failed to generate a complete plan (main meals not filled or early exit).")

    if best_plan:
        logger.info(
            f"Best plan found with score {best_plan_score:.2f}. Totals: C:{best_plan_totals['calories']:.0f}, P:{best_plan_totals['protein']:.0f}, C:{best_plan_totals['carbs']:.0f}, F:{best_plan_totals['fat']:.0f}")
        return {
            "plan_recipes": best_plan,  # Dict of {'breakfast': RecipeObj, ...}
            "plan_totals": best_plan_totals,
            "user_targets": user_daily_targets
        }
    else:
        logger.warning(
            "Could not find a suitable meal plan after all attempts.")
        return None
