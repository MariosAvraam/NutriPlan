import React from 'react';
import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import RegisterPage from './pages/RegisterPage';
import LoginPage from './pages/LoginPage';
import MealPlanPage from './pages/MealPlanPage';
import ProfilePage from './pages/ProfilePage';
import { useAuth } from './contexts/AuthContext';
import './App.css';

// Placeholder Pages (create these as simple components later)
const HomePage = () => <h2>Home Page</h2>;
const NotFoundPage = () => <h2>404 - Page Not Found</h2>;

function App() {
  const navigate = useNavigate();
  const { authToken, currentUser, logout, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading application...</div>; // Or a spinner component
  }
  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div>
      <nav>
        <ul>
          <li><Link to="/">Home</Link></li>
          {authToken ? (
            <>
              <li><Link to="/profile">Profile ({currentUser?.username})</Link></li>
              <li><Link to="/meal-plan">Meal Plan</Link></li>
              <li><button onClick={handleLogout}>Logout</button></li>
            </>
          ) : (
            <>
              <li><Link to="/login">Login</Link></li>
              <li><Link to="/register">Register</Link></li>
            </>
          )}
        </ul>
      </nav>
      <hr />
      <main>
        <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        {/* Protected Routes */}
        <Route 
          path="/profile" 
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/meal-plan" 
          element={
            <ProtectedRoute>
              <MealPlanPage />
            </ProtectedRoute>
          } 
        />
        
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      </main>
    </div>
  );
}

export default App;