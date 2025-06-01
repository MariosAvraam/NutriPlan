import logging
from django.contrib.auth.models import User
from api.models import UserProfile, Recipe  # Assuming your app is 'api'
from api.meal_planner_logic import generate_daily_meal_plan_v1  # Import your function

# Configure logging to see output in the shell
# DEBUG level will show more detailed logs from your algorithm
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s')
# Or use INFO for less verbosity:
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get a logger instance for any direct logging in shell
logger = logging.getLogger(__name__)

# Option A: Get by username (if you know it)
try:
    # Replace with an actual username
    test_user = User.objects.get(username='admin')
    test_user_profile = UserProfile.objects.get(user=test_user)
    print(f"Found profile for user: {test_user.username}")
    print(f"Targets - Calories: {test_user_profile.target_calories}, Prot%: {test_user_profile.target_protein_percent}, Carb%: {test_user_profile.target_carbs_percent}, Fat%: {test_user_profile.target_fat_percent}")
except User.DoesNotExist:
    print("Test user not found. Please create one or use an existing one.")
    test_user_profile = None
except UserProfile.DoesNotExist:
    print(
        f"UserProfile for {test_user.username} not found. Creating one with default values.")
    # If profile doesn't exist, you might want to create it for testing
    test_user_profile, created = UserProfile.objects.get_or_create(
        user=test_user)
    if created:
        print("Default profile created. You might want to set targets via admin or shell before testing fully.")
    # To set targets directly in shell (example):
    # test_user_profile.target_calories = 2200
    # test_user_profile.target_protein_percent = 30
    # test_user_profile.target_carbs_percent = 40
    # test_user_profile.target_fat_percent = 30
    # test_user_profile.save()
    # print("Targets set for test user profile.")

# Ensure you have a profile to work with
if not test_user_profile:
    print("Cannot proceed without a UserProfile. Please ensure one exists and is configured.")
else:
    # You are ready to call the function
    pass

print(
    f"Total recipes with calculated nutrition: {Recipe.objects.filter(total_calories__isnull=False).count()}")
for meal_type_choice in Recipe.MEAL_TYPE_CHOICES:
    meal_code = meal_type_choice[0]
    print(
        f"Recipes for {meal_code}: {Recipe.objects.filter(meal_type=meal_code, total_calories__isnull=False).count()}")

if test_user_profile:
    print("\n--- Calling generate_daily_meal_plan_v1 ---")
    generated_plan_data = generate_daily_meal_plan_v1(test_user_profile)
    print("--- Function Call Finished ---")

    if generated_plan_data:
        print("\n--- Generated Plan Data ---")
        print(f"User Targets: {generated_plan_data['user_targets']}")
        print(f"Plan Totals: {generated_plan_data['plan_totals']}")
        print("\nAssigned Recipes:")
        for meal_slot, recipe_obj in generated_plan_data['plan_recipes'].items():
            if recipe_obj:
                print(
                    f"  {meal_slot.capitalize()}: {recipe_obj.name} (Calories: {recipe_obj.total_calories}, Protein: {recipe_obj.total_protein_g}g)")
            else:
                print(f"  {meal_slot.capitalize()}: None assigned")
    else:
        print("\n--- Meal Plan Generation FAILED ---")
        print("No suitable plan was found. Check logs for details.")
else:
    print("Skipping meal plan generation as test_user_profile is not set.")
