from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.html import format_html
from .models import Ingredient, Recipe, RecipeIngredient, UserProfile


# --- Ingredient Admin ---
@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'fdc_id',
        'calories_per_100g',
        'protein_per_100g',
        'carbs_per_100g',
        'fat_per_100g',
        'base_unit'
    )
    ordering = ['name']
    search_fields = ('name', 'fdc_id')
    list_filter = ('base_unit',)
    fieldsets = (
        (None, {
            'fields': ('name', 'fdc_id', 'base_unit')
        }),
        ('Nutritional Information (per 100g)', {
            'fields': ('calories_per_100g', 'protein_per_100g', 'carbs_per_100g', 'fat_per_100g')
        }),
        ('USDA Data (Advanced)', {
            'classes': ('collapse',),
            'fields': ('usda_food_portions',)
        }),
    )


# --- RecipeIngredient Inline ---
# This allows managing RecipeIngredients directly within the Recipe admin page
class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1  # Number of empty forms to display for adding new ingredients
    autocomplete_fields = ['ingredient']
    fields = ('ingredient', 'quantity', 'unit')

    def get_queryset(self, request):
        # Optimize query to prefetch related ingredient for display
        return super().get_queryset(request).select_related('ingredient')


# --- Recipe Admin ---
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'meal_type',
        'display_total_calories',
        'total_protein_g',
        'total_carbs_g',
        'total_fat_g'
    )
    list_filter = ('meal_type',)
    search_fields = ('name', 'description', 'instructions', 'health_insights')
    inlines = [RecipeIngredientInline]

    # Fields to be displayed as read-only in the admin form
    readonly_fields = (
        'total_calories',
        'total_protein_g',
        'total_carbs_g',
        'total_fat_g'
    )

    fieldsets = (
        (None, {
            'fields': ('name', 'meal_type', 'description', 'instructions')
        }),
        ('Health & Insights', {
            'fields': ('health_insights',)
        }),
        # Optional fields (if you uncomment them in models.py)
        # ('Timings & Servings', {
        #     'fields': ('prep_time_minutes', 'cook_time_minutes', 'servings')
        # }),
        ('Calculated Nutritional Information (Total)', {
            'classes': ('collapse',),
            'fields': readonly_fields
        }),
    )

    actions = ['recalculate_nutrition_action']

    def display_total_calories(self, obj):
        return f"{obj.total_calories} kcal" if obj.total_calories is not None else "N/A"
    display_total_calories.short_description = 'Total Calories'
    # Allows sorting by this column
    display_total_calories.admin_order_field = 'total_calories'

    def recalculate_nutrition_action(self, request, queryset):
        updated_count = 0
        for recipe in queryset:
            recipe.calculate_nutrition(save_to_instance=True)
            updated_count += 1
        self.message_user(
            request, f"Recalculated nutrition for {updated_count} recipe(s).")
    recalculate_nutrition_action.short_description = "Recalculate nutrition for selected recipes"

    def get_queryset(self, request):
        # Prefetch related ingredients to optimize admin display and reduce queries
        # especially if you display something from ingredients in list_display
        return super().get_queryset(request).prefetch_related('ingredient_details__ingredient')


# --- RecipeIngredient Admin ---
@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'quantity', 'unit')
    list_filter = ('unit', )
    autocomplete_fields = ['recipe', 'ingredient']
    search_fields = ('recipe__name', 'ingredient__name')


# --- UserProfile Admin ---
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'target_calories', 'target_protein_percent',
                    'target_carbs_percent', 'target_fat_percent')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('user',)

    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        ('Nutritional Targets', {
            'fields': (('target_calories',),
                       ('target_protein_percent', 'target_carbs_percent', 'target_fat_percent'))
        }),
        # Optional fields (if you uncomment them in models.py)
        # ('Dietary Information', {
        #     'fields': ('dietary_preferences',)
        # }),
    )

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'
    get_username.admin_order_field = 'user__username'

    def get_queryset(self, request):
        # Optimize query to prefetch related user
        return super().get_queryset(request).select_related('user')
