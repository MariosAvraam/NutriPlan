import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1/';

// Create an Axios instance
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to add the auth token to requests if available
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers['Authorization'] = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const registerUser = (userData) => {
  return apiClient.post('auth/register/', userData);
};

export const loginUser = (credentials) => {
  return apiClient.post('auth/login/', credentials);
};

// Placeholder for fetching user profile - to be used by UserProfile page
export const fetchUserProfile = () => {
  return apiClient.get('profile/');
};

// Placeholder for updating user profile
export const updateUserProfile = (profileData) => {
  return apiClient.put('profile/', profileData);
};


// Add other API functions here as needed (e.g., for recipes, meal plans)
export const fetchRecipes = () => {
    return apiClient.get('recipes/');
};

export const generateMealPlan = () => { // No data needed for POST if it reads from profile
    return apiClient.post('mealplan/generate/');
};


export default apiClient;