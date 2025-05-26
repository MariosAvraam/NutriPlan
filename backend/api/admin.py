from django.contrib import admin
from .models import Ingredient, Recipe, RecipeIngredient, UserProfile

# Basic registration
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(RecipeIngredient)
admin.site.register(UserProfile)

# You can customize how these appear in the admin later if needed,
# for example, using ModelAdmin classes:

# class RecipeIngredientInline(admin.TabularInline): # Or StackedInline
#     model = RecipeIngredient
#     extra = 1 # Number of empty forms to display

# class RecipeAdmin(admin.ModelAdmin):
#     list_display = ('name', 'meal_type', 'total_calories')
#     list_filter = ('meal_type',)
#     search_fields = ('name', 'description')
#     inlines = [RecipeIngredientInline] # Allows adding ingredients directly when creating/editing a recipe

# class IngredientAdmin(admin.ModelAdmin):
#     list_display = ('name', 'calories_per_100g', 'protein_per_100g', 'carbs_per_100g', 'fat_per_100g')
#     search_fields = ('name',)

# # If you want to use the custom admin classes, unregister the basic ones first
# # or just register with the custom class directly:
# # admin.site.unregister(Recipe) # If already registered simply
# # admin.site.register(Recipe, RecipeAdmin)
# # admin.site.unregister(Ingredient)
# # admin.site.register(Ingredient, IngredientAdmin)
