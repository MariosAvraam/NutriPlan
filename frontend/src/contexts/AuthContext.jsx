import React, { createContext, useContext, useState, useEffect } from 'react';
import apiClient, { fetchUserProfile } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [authToken, setAuthToken] = useState(localStorage.getItem('authToken'));
  const [currentUser, setCurrentUser] = useState(null); // To store user details like username, email
  const [isLoading, setIsLoading] = useState(true); // For initial auth check
  

  useEffect(() => {
    const loadUser = async () => {
      if (authToken) {
        apiClient.defaults.headers.common['Authorization'] = `Token ${authToken}`;
        try {
          const response = await fetchUserProfile(); // Fetch profile on load if token exists
          setCurrentUser(response.data); // Assuming profile endpoint returns user profile data
          // If your login endpoint returns user details, you might not need this separate fetch here
          // Or if fetchUserProfile IS the one that returns the user object directly
        } catch (error) {
          console.error("Failed to fetch user profile on load", error);
          // Token might be invalid/expired, so clear it
          localStorage.removeItem('authToken');
          setAuthToken(null);
          setCurrentUser(null);
          delete apiClient.defaults.headers.common['Authorization'];
        }
      }
      setIsLoading(false);
    };
    loadUser();
  }, [authToken]); // Re-run if authToken changes (e.g. on login/logout)

  const login = (token, userData) => {
    localStorage.setItem('authToken', token);
    setAuthToken(token);
    setCurrentUser(userData);
    apiClient.defaults.headers.common['Authorization'] = `Token ${token}`;
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    setAuthToken(null);
    setCurrentUser(null);
    delete apiClient.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ authToken, currentUser, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  return useContext(AuthContext);
};