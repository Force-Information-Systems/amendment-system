/**
 * Simple QA Dashboard Test - Minimal version to debug loading issue
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

// Get API base URL from environment or default to /api (for proxy)
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const QADashboardSimple = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  useEffect(() => {
    console.log('QA Dashboard Simple mounted');
    testLoad();
  }, []);

  const testLoad = async () => {
    console.log('Starting data load test...');
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      console.log('Token exists:', !!token);

      if (!token) {
        console.error('No token found');
        setError('Not logged in. Please login first.');
        setLoading(false);
        return;
      }

      console.log('Fetching amendments...');
      const response = await fetch(`${API_BASE_URL}/amendments?limit=5`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Fetch failed:', response.status, errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const result = await response.json();
      console.log('Data loaded:', result);
      setData(result);
      setLoading(false);

    } catch (err) {
      console.error('Error in testLoad:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  console.log('Rendering QADashboardSimple - loading:', loading, 'error:', error, 'data:', !!data);

  if (loading) {
    return (
      <div style={{ padding: '20px' }}>
        <h1>QA Dashboard (Simple Test)</h1>
        <p>Loading... Check browser console for details.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px' }}>
        <h1>QA Dashboard (Simple Test)</h1>
        <p style={{ color: 'red' }}>Error: {error}</p>
        <p>Check browser console (F12) for details.</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <h1>QA Dashboard (Simple Test)</h1>
      <p style={{ color: 'green' }}>✓ Data loaded successfully!</p>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
};

export default QADashboardSimple;
