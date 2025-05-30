import React, { useState, useEffect, useCallback } from 'react';
import { fetchUserProfile, updateUserProfile } from '../services/api'; 
import { useAuth } from '../contexts/AuthContext';

const ProfilePage = () => {
  const { currentUser } = useAuth(); // Get currentUser to ensure context is ready
  const [profileData, setProfileData] = useState({
    target_calories: '',
    target_protein_percent: '',
    target_carbs_percent: '',
    target_fat_percent: '',
    // Add other fields from UserProfileSerializer if needed
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Use useCallback to memoize fetchProfile function
  const fetchProfile = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await fetchUserProfile();
      setProfileData({
        target_calories: response.data.target_calories || '',
        target_protein_percent: response.data.target_protein_percent || '',
        target_carbs_percent: response.data.target_carbs_percent || '',
        target_fat_percent: response.data.target_fat_percent || '',
      });
    } catch (err) {
      console.error("Failed to fetch profile:", err.response ? err.response.data : err.message);
      setError("Could not load your profile data. Please try again later.");
    } finally {
      setIsLoading(false);
    }
  }, []); // Empty dependency array means this function is created once

  useEffect(() => {
    // Only fetch profile if currentUser is loaded (meaning auth check is done)
    // and to prevent fetching if user navigates away and comes back quickly
    // or if component re-renders for other reasons unnecessarily.
    if (currentUser) { // currentUser from useAuth indicates auth state is resolved
        fetchProfile();
    }
  }, [currentUser, fetchProfile]); // Depend on currentUser and fetchProfile

  const handleChange = (e) => {
    const { name, value } = e.target;
    setProfileData(prevData => ({
      ...prevData,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsLoading(true); // Indicate loading during submission

    // Basic frontend validation for percentages
    const protein = parseFloat(profileData.target_protein_percent);
    const carbs = parseFloat(profileData.target_carbs_percent);
    const fat = parseFloat(profileData.target_fat_percent);

    if (protein + carbs + fat !== 100) {
        setError('Macro percentages (protein, carbs, fat) must add up to 100%.');
        setIsLoading(false);
        return;
    }

    try {
      const dataToUpdate = {
        target_calories: parseInt(profileData.target_calories, 10),
        target_protein_percent: protein,
        target_carbs_percent: carbs,
        target_fat_percent: fat,
      };
      const response = await updateUserProfile(dataToUpdate);
      setProfileData({ // Update local state with potentially formatted data from response
        target_calories: response.data.target_calories || '',
        target_protein_percent: response.data.target_protein_percent || '',
        target_carbs_percent: response.data.target_carbs_percent || '',
        target_fat_percent: response.data.target_fat_percent || '',
      });
      setSuccess('Profile updated successfully!');
    } catch (err) {
      console.error("Failed to update profile:", err.response ? err.response.data : err.message);
      if (err.response && err.response.data) {
        const errorData = err.response.data;
        let errorMessages = [];
        for (const key in errorData) {
          errorMessages.push(`${key}: ${errorData[key].join ? errorData[key].join(', ') : errorData[key]}`);
        }
        setError(errorMessages.join(' | '));
      } else {
        setError('Failed to update profile. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading && !profileData.target_calories) { // Show loading only if data hasn't been fetched yet
    return <div>Loading profile...</div>;
  }

  return (
    <div>
      <h2>Your Nutritional Profile</h2>
      {currentUser && <p>Manage targets for: <strong>{currentUser.username}</strong></p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {success && <p style={{ color: 'green' }}>{success}</p>}
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="target_calories">Target Daily Calories:</label>
          <input
            type="number"
            id="target_calories"
            name="target_calories"
            value={profileData.target_calories}
            onChange={handleChange}
            min="0"
            required
          />
        </div>
        <div>
          <label htmlFor="target_protein_percent">Target Protein (% of Calories):</label>
          <input
            type="number"
            id="target_protein_percent"
            name="target_protein_percent"
            value={profileData.target_protein_percent}
            onChange={handleChange}
            min="0"
            max="100"
            step="0.1"
            required
          />
        </div>
        <div>
          <label htmlFor="target_carbs_percent">Target Carbohydrates (% of Calories):</label>
          <input
            type="number"
            id="target_carbs_percent"
            name="target_carbs_percent"
            value={profileData.target_carbs_percent}
            onChange={handleChange}
            min="0"
            max="100"
            step="0.1"
            required
          />
        </div>
        <div>
          <label htmlFor="target_fat_percent">Target Fat (% of Calories):</label>
          <input
            type="number"
            id="target_fat_percent"
            name="target_fat_percent"
            value={profileData.target_fat_percent}
            onChange={handleChange}
            min="0"
            max="100"
            step="0.1"
            required
          />
        </div>
        <button type="submit" disabled={isLoading}>
          {isLoading && !profileData.target_calories ? 'Loading...' : (isLoading ? 'Saving...' : 'Update Profile')}
        </button>
      </form>
    </div>
  );
};

export default ProfilePage;