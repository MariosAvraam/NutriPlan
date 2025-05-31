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

export const fetchUserProfile = () => {
  return apiClient.get('profile/');
};

export const updateUserProfile = (profileData) => {
  return apiClient.put('profile/', profileData);
};

export const fetchRecipes = () => {
    return apiClient.get('recipes/');
};

export const generateMealPlan = () => {
    return apiClient.post('mealplan/generate/');
};


export default apiClient;