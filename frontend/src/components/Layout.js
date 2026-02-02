import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Layout.css';

function Layout({ children }) {
  const location = useLocation();
  const { user, logout, isAdmin } = useAuth();

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <h1 className="logo">
            <Link to="/dashboard">Amendment System</Link>
          </h1>
          <nav className="nav">
            <Link
              to="/dashboard"
              className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}
            >
              Dashboard
            </Link>
            <Link
              to="/amendments"
              className={`nav-link ${isActive('/amendments') ? 'active' : ''}`}
            >
              Amendments
            </Link>
            <Link
              to="/qa-dashboard"
              className={`nav-link ${isActive('/qa-dashboard') ? 'active' : ''}`}
            >
              QA Dashboard
            </Link>
            {isAdmin() && (
              <Link
                to="/admin"
                className={`nav-link ${isActive('/admin') ? 'active' : ''}`}
              >
                Admin
              </Link>
            )}
          </nav>
          <div className="user-info">
            <span className="user-name">Welcome, {user?.employee_name}</span>
            <span className="user-role">({user?.role})</span>
            <button onClick={logout} className="btn-logout">
              Logout
            </button>
          </div>
        </div>
      </header>
      <main className="main-content">
        {children}
      </main>
      <footer className="footer">
        <div className="footer-content">
          <p>&copy; 2025 Amendment System. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

export default Layout;
