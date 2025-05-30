
from .pre_vetted_ingredients import PRE_VETTED_INGREDIENTS
from api.models import Ingredient
from django.core.management.base import BaseCommand
import requests
import time
import logging
from dotenv import load_dotenv
import os
load_dotenv()


# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- CONFIGURATION ---

USDA_API_KEY = os.getenv("USDA_API_KEY")
if not USDA_API_KEY:
    logger.error("USDA_API_KEY not found in .env file.")
    exit()

# Nutrient IDs we are interested in
NUTRIENT_MAP = {
    # Energy (kcal), Energy Atwater Specific, Energy Atwater General
    'calories': (1008, 2048, 2047),
    'protein': (1003,),
    'fat': (1004,),      # Total lipid (fat)
    'carbs': (1005,)     # Carbohydrate, by difference
}

API_BASE_URL = "https://api.nal.usda.gov/fdc/v1/food/"
REQUEST_DELAY_SECONDS = 2


class Command(BaseCommand):
    help = 'Populates the Ingredient database with data from USDA FDC API using a pre-vetted list of FDC IDs.'

    def handle(self, *args, **options):
        if not USDA_API_KEY:
            logger.error("Exiting: USDA_API_KEY is not configured.")
            return

        logger.info("Starting ingredient population process...")
        ingredients_added = 0
        ingredients_updated = 0
        ingredients_failed = 0

        for common_name, fdc_id_str in PRE_VETTED_INGREDIENTS:
            try:
                current_fdc_id = int(fdc_id_str)
            except ValueError:
                logger.error(
                    f"Invalid FDC ID format: {fdc_id_str} for {common_name}. Skipping.")
                ingredients_failed += 1
                continue

            logger.info(
                f"Processing: {common_name} (FDC ID: {current_fdc_id})")
            try:
                params = {
                    'api_key': USDA_API_KEY,
                    'format': 'full'
                }
                response = requests.get(
                    f"{API_BASE_URL}{current_fdc_id}", params=params)
                response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
                data = response.json()

                # --- Extract required nutrients ---
                nutrients_data = {}
                found_all_core_macros = True

                for key, ids_tuple in NUTRIENT_MAP.items():
                    nutrient_found = False
                    for nutrient_id_to_check in ids_tuple:
                        for nutrient_entry in data.get('foodNutrients', []):
                            if nutrient_entry.get('nutrient', {}).get('id') == nutrient_id_to_check:
                                # We assume data is per 100g as per USDA standard for these core nutrients
                                nutrients_data[key] = nutrient_entry.get(
                                    'amount', 0.0)
                                nutrient_found = True
                                break  # Found the preferred ID for this nutrient type
                        if nutrient_found:
                            # Moved to the next nutrient type (calories, protein, etc.)
                            break

                    # Core macros
                    if not nutrient_found and key in ['protein', 'fat', 'carbs']:
                        logger.warning(
                            f"Core nutrient '{key}' not found for {common_name} (FDC ID: {current_fdc_id}). Skipping this ingredient.")
                        found_all_core_macros = False
                        break  # Stop processing this ingredient if a core macro is missing

                if not found_all_core_macros:
                    ingredients_failed += 1
                    continue  # Skip to the next ingredient in the pre-vetted list

                # --- Extract and store foodPortions ---
                food_portions_data = data.get('foodPortions', [])

                # Get the official description from API
                ingredient_api_description = data.get(
                    'description', common_name).strip()

                # Create or update the ingredient in the database
                ingredient_obj, created = Ingredient.objects.update_or_create(
                    fdc_id=current_fdc_id,
                    defaults={
                        'name': ingredient_api_description,
                        'calories_per_100g': nutrients_data.get('calories', 0.0),
                        'protein_per_100g': nutrients_data.get('protein', 0.0),
                        'fat_per_100g': nutrients_data.get('fat', 0.0),
                        'carbs_per_100g': nutrients_data.get('carbs', 0.0),
                        'usda_food_portions': food_portions_data,
                        # 'base_unit' is already 'g' by default
                    }
                )

                if created:
                    logger.info(
                        f"CREATED: {ingredient_obj.name} with FDC ID {current_fdc_id}")
                    ingredients_added += 1
                else:
                    logger.info(
                        f"UPDATED: {ingredient_obj.name} with FDC ID {current_fdc_id}")
                    ingredients_updated += 1

            except requests.exceptions.HTTPError as e:
                logger.error(
                    f"HTTP error for {common_name} (FDC ID: {current_fdc_id}): {e.response.status_code} - {e.response.text}")
                ingredients_failed += 1
            except requests.exceptions.RequestException as e:
                logger.error(
                    f"Request failed for {common_name} (FDC ID: {current_fdc_id}): {e}")
                ingredients_failed += 1
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred for {common_name} (FDC ID: {current_fdc_id}): {e}")
                ingredients_failed += 1

            logger.info(
                f"Waiting for {REQUEST_DELAY_SECONDS} seconds before next request...")
            time.sleep(REQUEST_DELAY_SECONDS)

        logger.info("Ingredient population process finished.")
        logger.info(
            f"Summary: Added: {ingredients_added}, Updated: {ingredients_updated}, Failed: {ingredients_failed}")
