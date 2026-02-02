import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { amendmentAPI } from '../services/api';
import './Dashboard.css';

function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [versionStats, setVersionStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const [statsResponse, versionStatsResponse] = await Promise.all([
        amendmentAPI.getStats(),
        amendmentAPI.getVersionStats(),
      ]);
      setStats(statsResponse.data);
      setVersionStats(versionStatsResponse.data || []);
      setError(null);
    } catch (err) {
      setError('Failed to load statistics: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (!stats) {
    return <div className="error">No statistics available</div>;
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Overview of amendment statistics</p>
      </div>

      <div className="stats-grid">
        <Link to="/amendments" className="stat-card total stat-card-link">
          <div className="stat-label">Total Amendments</div>
          <div className="stat-value">{stats.total_amendments}</div>
        </Link>

        <Link to="/amendments?qa_completed=true" className="stat-card stat-card-link">
          <div className="stat-label">QA Completed</div>
          <div className="stat-value">{stats.qa_completed}</div>
        </Link>

        <Link to="/amendments?database_changes=true" className="stat-card stat-card-link">
          <div className="stat-label">Database Changes</div>
          <div className="stat-value">{stats.database_changes}</div>
        </Link>

        <Link to="/amendments?db_upgrade_changes=true" className="stat-card stat-card-link">
          <div className="stat-label">DB Upgrade Changes</div>
          <div className="stat-value">{stats.db_upgrade_changes}</div>
        </Link>
      </div>

      <div className="stats-section">
        <div className="stat-group">
          <h2 className="stat-group-title">By Status</h2>
          <div className="stat-list">
            {Object.entries(stats.by_status).map(([status, count]) => (
              <Link
                key={status}
                to={`/amendments?amendment_status=${encodeURIComponent(status)}`}
                className="stat-item stat-item-link"
              >
                <span className="stat-item-label">{status}</span>
                <span className={`stat-item-value status-${status.toLowerCase().replace(' ', '-')}`}>
                  {count}
                </span>
              </Link>
            ))}
          </div>
        </div>

        <div className="stat-group">
          <h2 className="stat-group-title">By Priority</h2>
          <div className="stat-list">
            {Object.entries(stats.by_priority).map(([priority, count]) => (
              <Link
                key={priority}
                to={`/amendments?priority=${encodeURIComponent(priority)}`}
                className="stat-item stat-item-link"
              >
                <span className="stat-item-label">{priority}</span>
                <span className={`stat-item-value priority-${priority.toLowerCase()}`}>
                  {count}
                </span>
              </Link>
            ))}
          </div>
        </div>

        <div className="stat-group">
          <h2 className="stat-group-title">By Type</h2>
          <div className="stat-list">
            {Object.entries(stats.by_type).map(([type, count]) => (
              <Link
                key={type}
                to={`/amendments?amendment_type=${encodeURIComponent(type)}`}
                className="stat-item stat-item-link"
              >
                <span className="stat-item-label">{type}</span>
                <span className="stat-item-value">{count}</span>
              </Link>
            ))}
          </div>
        </div>

        <div className="stat-group">
          <h2 className="stat-group-title">By Development Status</h2>
          <div className="stat-list">
            {Object.entries(stats.by_development_status).map(([status, count]) => (
              <Link
                key={status}
                to={`/amendments?development_status=${encodeURIComponent(status)}`}
                className="stat-item stat-item-link"
              >
                <span className="stat-item-label">{status}</span>
                <span className="stat-item-value">{count}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {versionStats.length > 0 && (
        <div className="stats-section" style={{ display: 'block', marginTop: '3rem' }}>
          <h2 className="section-title">Amendments by Application Version</h2>
          <div className="version-stats-grid">
            {versionStats.map((stat, idx) => (
              <div
                key={idx}
                className="version-stat-card"
                onClick={() => {
                  const params = new URLSearchParams({ application: stat.application_name });
                  navigate(`/amendments?${params.toString()}`);
                }}
                style={{ cursor: 'pointer' }}
              >
                <div className="version-stat-header">
                  <span className="version-app-name">{stat.application_name}</span>
                  <span className="version-number">{stat.version}</span>
                </div>
                <div className="version-stat-count">{stat.amendment_count}</div>
                <div className="version-stat-label">
                  {stat.amendment_count === 1 ? 'amendment' : 'amendments'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="dashboard-actions">
        <Link to="/amendments" className="btn btn-primary">
          View All Amendments
        </Link>
        <Link to="/amendments/new" className="btn btn-secondary">
          Create New Amendment
        </Link>
      </div>
    </div>
  );
}

export default Dashboard;
