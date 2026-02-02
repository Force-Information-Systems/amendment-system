import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import AmendmentList from './pages/AmendmentList';
import AmendmentDetail from './pages/AmendmentDetail';
import AmendmentCreate from './pages/AmendmentCreate';
import Dashboard from './pages/Dashboard';
import QADashboard from './pages/QADashboard';
import QADashboardDebug from './pages/QADashboardDebug';
import Admin from './pages/Admin';
import AdminApplications from './pages/AdminApplications';
import AdminVersions from './pages/AdminVersions';
import AdminEmployees from './pages/AdminEmployees';
import AdminReference from './pages/AdminReference';
import './App.css';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public route */}
          <Route path="/login" element={<Login />} />

          {/* Protected routes */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Layout><Dashboard /></Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/amendments"
            element={
              <ProtectedRoute>
                <Layout><AmendmentList /></Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/amendments/new"
            element={
              <ProtectedRoute>
                <Layout><AmendmentCreate /></Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/amendments/:id"
            element={
              <ProtectedRoute>
                <Layout><AmendmentDetail /></Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/qa-dashboard"
            element={
              <ProtectedRoute>
                <Layout><QADashboard /></Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/qa-dashboard-debug"
            element={
              <ProtectedRoute>
                <Layout><QADashboardDebug /></Layout>
              </ProtectedRoute>
            }
          />

          {/* Admin routes - require admin role */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute adminOnly={true}>
                <Layout><Admin /></Layout>
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/admin/applications" replace />} />
            <Route path="applications" element={<AdminApplications />} />
            <Route path="versions" element={<AdminVersions />} />
            <Route path="employees" element={<AdminEmployees />} />
            <Route path="reference" element={<AdminReference />} />
          </Route>
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
