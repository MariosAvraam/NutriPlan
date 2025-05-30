import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerUser } from '../services/api';

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      // Basic frontend validation (add more as needed)
      if (!formData.username || !formData.password || !formData.email) {
        setError('Username, email, and password are required.');
        return;
      }
      // You might want to add password confirmation here on the frontend too

      const response = await registerUser(formData);
      console.log('Registration successful:', response.data);
      setSuccess('Registration successful! Please log in.');
      // Optionally clear form or navigate to login after a delay
      // navigate('/login'); 
    } catch (err) {
      console.error('Registration error:', err.response ? err.response.data : err.message);
      if (err.response && err.response.data) {
        // Convert backend error object to a readable string
        const errorData = err.response.data;
        let errorMessages = [];
        for (const key in errorData) {
          errorMessages.push(`${key}: ${errorData[key].join ? errorData[key].join(', ') : errorData[key]}`);
        }
        setError(errorMessages.join(' | '));
      } else {
        setError('Registration failed. Please try again.');
      }
    }
  };

  return (
    <div>
      <h2>Register</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {success && <p style={{ color: 'green' }}>{success}</p>}
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="username">Username:</label>
          <input type="text" id="username" name="username" value={formData.username} onChange={handleChange} required />
        </div>
        <div>
          <label htmlFor="email">Email:</label>
          <input type="email" id="email" name="email" value={formData.email} onChange={handleChange} required />
        </div>
        <div>
          <label htmlFor="password">Password:</label>
          <input type="password" id="password" name="password" value={formData.password} onChange={handleChange} required />
        </div>
        {/* Optional: Add password confirmation field here */}
        <div>
          <label htmlFor="first_name">First Name:</label>
          <input type="text" id="first_name" name="first_name" value={formData.first_name} onChange={handleChange} />
        </div>
        <div>
          <label htmlFor="last_name">Last Name:</label>
          <input type="text" id="last_name" name="last_name" value={formData.last_name} onChange={handleChange} />
        </div>
        <button type="submit">Register</button>
      </form>
    </div>
  );
};

export default RegisterPage;