import React, { useState, useEffect, useCallback } from 'react';
import { generateMealPlan } from '../services/api'; 
import { useAuth } from '../contexts/AuthContext';

// A simple component to display a single recipe's details
const RecipeCard = ({ recipe }) => {
  if (!recipe) return <p>No recipe assigned for this meal.</p>;
  return (
    <div style={{ border: '1px solid #ccc', margin: '10px', padding: '10px' }}>
      <h4>{recipe.name}</h4>
      <p><strong>Meal Type:</strong> {recipe.meal_type}</p>
      <p><strong>Calories:</strong> {recipe.total_calories?.toFixed(0) || 'N/A'}</p>
      <p><strong>Protein:</strong> {recipe.total_protein_g?.toFixed(1) || 'N/A'}g</p>
      <p><strong>Carbs:</strong> {recipe.total_carbs_g?.toFixed(1) || 'N/A'}g</p>
      <p><strong>Fat:</strong> {recipe.total_fat_g?.toFixed(1) || 'N/A'}g</p>
      <h5>Ingredients:</h5>
      <ul>
        {recipe.ingredient_details?.map(ing => (
          <li key={ing.id}>
            {ing.quantity} {ing.unit} {ing.ingredient.name}
          </li>
        ))}
      </ul>
      <h5>Instructions:</h5>
      <pre style={{ whiteSpace: 'pre-wrap' }}>{recipe.instructions}</pre>
      {recipe.health_insights && (
        <>
          <h5>Health Insights:</h5>
          <p>{recipe.health_insights}</p>
        </>
      )}
    </div>
  );
};


const MealPlanPage = () => {
  const { authToken } = useAuth(); // We need authToken to know if user is logged in
  const [mealPlan, setMealPlan] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGeneratePlan = useCallback(async () => {
    if (!authToken) {
      setError("Please log in to generate a meal plan.");
      return;
    }
    setIsLoading(true);
    setError('');
    setMealPlan(null); // Clear previous plan
    try {
      const response = await generateMealPlan(); // POST request
      setMealPlan(response.data);
    } catch (err) {
      console.error("Failed to generate meal plan:", err.response ? err.response.data : err.message);
      setError("Could not generate meal plan. Ensure your profile is complete and try again. " +
               (err.response?.data?.error || ""));
    } finally {
      setIsLoading(false);
    }
  }, [authToken]); // Depend on authToken

  // Optionally, fetch a plan when the component mounts if a plan was previously generated
  // Or if you want to auto-generate on page load. For now, let's use a button.
  // useEffect(() => {
  //   if (authToken) { // Only attempt if user is logged in
  //     handleGeneratePlan();
  //   }
  // }, [authToken, handleGeneratePlan]); // Re-fetch if auth token changes or if handleGeneratePlan changes

  return (
    <div>
      <h2>Your Daily Meal Plan</h2>
      <button onClick={handleGeneratePlan} disabled={isLoading || !authToken}>
        {isLoading ? 'Generating...' : 'Generate New Meal Plan'}
      </button>
      {!authToken && <p>Please <a href="/login">log in</a> to generate a meal plan.</p>}

      {error && <p style={{ color: 'red' }}>Error: {error}</p>}

      {console.log(mealPlan)}

      {isLoading && <p>Loading meal plan...</p>}

      {mealPlan && !isLoading && (
        <div>
          <h3>Daily Targets:</h3>
          <p>Calories: {mealPlan.daily_targets?.calories}</p>
          <p>Protein: {mealPlan.daily_targets?.protein_percent}%</p>
          <p>Carbs: {mealPlan.daily_targets?.carbs_percent}%</p>
          <p>Fat: {mealPlan.daily_targets?.fat_percent}%</p>

          <h3>Meals:</h3>
          <div>
            <h4>Breakfast</h4>
            {mealPlan.meals?.breakfast ? <RecipeCard recipe={mealPlan.meals.breakfast} /> : <p>No breakfast assigned.</p>}
          </div>
          <div>
            <h4>Lunch</h4>
            {mealPlan.meals?.lunch ? <RecipeCard recipe={mealPlan.meals.lunch} /> : <p>No lunch assigned.</p>}
          </div>
          <div>
            <h4>Dinner</h4>
            {mealPlan.meals?.dinner ? <RecipeCard recipe={mealPlan.meals.dinner} /> : <p>No dinner assigned.</p>}
          </div>
          <div>
            <h4>Snacks</h4>
            {mealPlan.meals?.snacks && mealPlan.meals.snacks.length > 0 ? (
              mealPlan.meals.snacks.map((snack, index) => <RecipeCard key={index} recipe={snack} />)
            ) : (
              <p>No snacks assigned.</p>
            )}
          </div>

          <h3>Estimated Totals for the Day:</h3>
          <p>Calories: {mealPlan.totals_for_the_day?.calories?.toFixed(0) || 'N/A'}</p>
          <p>Protein: {mealPlan.totals_for_the_day?.protein_g?.toFixed(1) || 'N/A'}g</p>
          {/* Add carbs and fat totals similarly */}
        </div>
      )}
    </div>
  );
};

export default MealPlanPage;