import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { loginUser } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const LoginPage = () => {
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      if (!formData.username || !formData.password) {
        setError('Username and password are required.');
        return;
      }
      const response = await loginUser(formData);
      // Assuming response.data = { token: '...', user_id: ..., username: ..., user_details: {...} }
      // from your CustomAuthToken view
      login(response.data.token, response.data.user_details || { id: response.data.user_id, username: response.data.username });
      navigate('/profile'); // Navigate to profile or dashboard on successful login
    } catch (err) {
      console.error('Login error:', err.response ? err.response.data : err.message);
      if (err.response && err.response.data && err.response.data.non_field_errors) {
         setError(err.response.data.non_field_errors.join(', '));
      } else if (err.response && err.response.data) {
        let errorMessages = [];
        for (const key in err.response.data) {
          errorMessages.push(`${key}: ${err.response.data[key].join ? err.response.data[key].join(', ') : err.response.data[key]}`);
        }
        setError(errorMessages.join(' | '));
      }
      else {
        setError('Login failed. Please check your credentials.');
      }
    }
  };

  return (
    <div>
      <h2>Login</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="username">Username:</label>
          <input type="text" id="username" name="username" value={formData.username} onChange={handleChange} required />
        </div>
        <div>
          <label htmlFor="password">Password:</label>
          <input type="password" id="password" name="password" value={formData.password} onChange={handleChange} required />
        </div>
        <button type="submit">Login</button>
      </form>
      <p>
        Don't have an account? <Link to="/register">Register here</Link>
      </p>
    </div>
  );
};

export default LoginPage;