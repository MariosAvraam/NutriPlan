import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { authToken, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>; // Or a proper loading spinner
  }

  if (!authToken) {
    // User not authenticated, redirect to login page
    // You can pass the current location to redirect back after login
    // return <Navigate to="/login" state={{ from: location }} replace />;
    return <Navigate to="/login" replace />;
  }

  // User is authenticated, render the child route component
  return children ? children : <Outlet />; // Outlet is used for nested routes
};

export default ProtectedRoute;