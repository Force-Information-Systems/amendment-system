import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import './Admin.css';

function Admin() {
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <div className="admin-container">
      <div className="admin-header">
        <h1>Administration</h1>
        <p>Manage system data and reference values</p>
      </div>

      <div className="admin-content">
        <nav className="admin-nav">
          <Link
            to="/admin/applications"
            className={`admin-nav-link ${isActive('/admin/applications') ? 'active' : ''}`}
          >
            Applications
          </Link>
          <Link
            to="/admin/versions"
            className={`admin-nav-link ${isActive('/admin/versions') ? 'active' : ''}`}
          >
            Application Versions
          </Link>
          <Link
            to="/admin/employees"
            className={`admin-nav-link ${isActive('/admin/employees') ? 'active' : ''}`}
          >
            Employees
          </Link>
          <Link
            to="/admin/reference"
            className={`admin-nav-link ${isActive('/admin/reference') ? 'active' : ''}`}
          >
            Reference Data
          </Link>
        </nav>

        <div className="admin-main">
          <Outlet />
        </div>
      </div>
    </div>
  );
}

export default Admin;
