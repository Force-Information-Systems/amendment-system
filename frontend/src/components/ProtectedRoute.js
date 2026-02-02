import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function ProtectedRoute({ children, adminOnly = false }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-container">
        <p>Loading...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (adminOnly && user.role !== 'Admin') {
    return (
      <div className="error-container">
        <h2>Access Denied</h2>
        <p>You do not have permission to access this page.</p>
        <p>Admin access required.</p>
      </div>
    );
  }

  return children;
}

export default ProtectedRoute;
