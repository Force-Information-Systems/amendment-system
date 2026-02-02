/**
 * QA Dashboard - Centralized QA Assignment Hub
 *
 * Features:
 * - View all QA assignments
 * - Filter by application, user, version, status, result
 * - Version grouping view
 * - Statistics cards
 * - Quick actions
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { StatusBadge } from '../components/qa';
import './QADashboard.css';

// Get API base URL from environment or default to /api (for proxy)
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const QADashboard = () => {
  const navigate = useNavigate();
  const [amendments, setAmendments] = useState([]);
  const [filteredAmendments, setFilteredAmendments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter states
  const [filters, setFilters] = useState({
    application: 'all',
    qaAssignedTo: 'all',
    version: 'all',
    qaStatus: 'all',
    qaOverallResult: 'all',
    searchText: '',
  });

  // UI states
  const [groupByVersion, setGroupByVersion] = useState(false);
  const [showMyAssignments, setShowMyAssignments] = useState(false);
  const [displayLimit, setDisplayLimit] = useState(25); // Start with 25 items

  // Dropdown options
  const [applications, setApplications] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [versions, setVersions] = useState([]);

  // Statistics
  const [stats, setStats] = useState({
    total: 0,
    notStarted: 0,
    assigned: 0,
    inTesting: 0,
    blocked: 0,
    passed: 0,
    failed: 0,
  });

  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    console.log('QA Dashboard mounting...');
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Reset display limit when filters change
  useEffect(() => {
    setDisplayLimit(25);
  }, [filters, showMyAssignments, groupByVersion]);

  const loadData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');

      if (!token) {
        setError('No authentication token found. Please login.');
        setLoading(false);
        return;
      }

      // Load amendments
      const amendmentsRes = await fetch(`${API_BASE_URL}/amendments?limit=1000`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!amendmentsRes.ok) {
        const errorText = await amendmentsRes.text();
        console.error('Amendments fetch failed:', amendmentsRes.status, errorText);
        throw new Error(`Failed to load amendments: ${amendmentsRes.status}`);
      }

      const amendmentsData = await amendmentsRes.json();
      console.log('Loaded amendments:', amendmentsData.items?.length || 0);
      setAmendments(amendmentsData.items || []);

      // Load applications
      const appsRes = await fetch(`${API_BASE_URL}/applications`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (appsRes.ok) {
        const appsData = await appsRes.json();
        console.log('Loaded applications:', appsData?.length || 0);
        setApplications(appsData || []);
      } else {
        console.warn('Failed to load applications:', appsRes.status);
      }

      // Load employees
      const employeesRes = await fetch(`${API_BASE_URL}/employees`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (employeesRes.ok) {
        const employeesData = await employeesRes.json();
        console.log('Loaded employees:', employeesData?.length || 0);
        setEmployees(employeesData || []);
      } else {
        console.warn('Failed to load employees:', employeesRes.status);
      }

      // Load versions
      const versionsRes = await fetch(`${API_BASE_URL}/versions`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (versionsRes.ok) {
        const versionsData = await versionsRes.json();
        console.log('Loaded versions:', versionsData?.length || 0);
        setVersions(versionsData || []);
      } else {
        console.warn('Failed to load versions:', versionsRes.status);
      }

      console.log('QA Dashboard loaded successfully');
      setLoading(false);
    } catch (err) {
      console.error('Error loading QA Dashboard data:', err);
      setError(`Failed to load QA dashboard data: ${err.message}`);
      setLoading(false);
    }
  };

  // Apply filters whenever amendments or filters change
  useEffect(() => {
    console.log('Applying filters...', {
      totalAmendments: amendments.length,
      filters,
      showMyAssignments
    });

    let filtered = [...amendments];

    // Filter by application
    if (filters.application !== 'all') {
      filtered = filtered.filter((a) => a.application === filters.application);
    }

    // Filter by QA assigned user
    if (filters.qaAssignedTo !== 'all') {
      const employeeId = parseInt(filters.qaAssignedTo);
      filtered = filtered.filter((a) => a.qa_assigned_id === employeeId);
    }

    // Show only my assignments
    if (showMyAssignments && currentUser.employee_id) {
      filtered = filtered.filter((a) => a.qa_assigned_id === currentUser.employee_id);
    }

    // Filter by version
    if (filters.version !== 'all') {
      filtered = filtered.filter((a) => a.version === filters.version);
    }

    // Filter by QA status
    if (filters.qaStatus !== 'all') {
      filtered = filtered.filter((a) => a.qa_status === filters.qaStatus);
    }

    // Filter by QA overall result
    if (filters.qaOverallResult !== 'all') {
      filtered = filtered.filter((a) => a.qa_overall_result === filters.qaOverallResult);
    }

    // Search text
    if (filters.searchText.trim()) {
      const searchLower = filters.searchText.toLowerCase();
      filtered = filtered.filter(
        (a) =>
          a.amendment_reference.toLowerCase().includes(searchLower) ||
          (a.description && a.description.toLowerCase().includes(searchLower))
      );
    }

    console.log('Filtered amendments:', filtered.length);
    setFilteredAmendments(filtered);
    calculateStats(filtered);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [amendments, filters, showMyAssignments]);

  const calculateStats = (data) => {
    const stats = {
      total: data.length,
      notStarted: data.filter((a) => a.qa_status === 'Not Started').length,
      assigned: data.filter((a) => a.qa_status === 'Assigned').length,
      inTesting: data.filter((a) => a.qa_status === 'In Testing').length,
      blocked: data.filter((a) => a.qa_status === 'Blocked').length,
      passed: data.filter((a) => a.qa_status === 'Passed').length,
      failed: data.filter((a) => a.qa_status === 'Failed').length,
    };
    setStats(stats);
  };

  const handleFilterChange = (field, value) => {
    setFilters({ ...filters, [field]: value });
  };

  const clearFilters = () => {
    setFilters({
      application: 'all',
      qaAssignedTo: 'all',
      version: 'all',
      qaStatus: 'all',
      qaOverallResult: 'all',
      searchText: '',
    });
    setShowMyAssignments(false);
  };

  const getAssignedEmployeeName = (employeeId) => {
    if (!employeeId) return 'Unassigned';
    const employee = employees.find((e) => e.employee_id === employeeId);
    return employee ? employee.employee_name : 'Unknown';
  };

  const groupAmendmentsByVersion = () => {
    const grouped = {};
    filteredAmendments.forEach((amendment) => {
      const version = amendment.version || 'No Version';
      if (!grouped[version]) {
        grouped[version] = [];
      }
      grouped[version].push(amendment);
    });
    return grouped;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Not set';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  };

  console.log('QA Dashboard rendering - loading:', loading, 'error:', error, 'amendments:', amendments.length, 'filtered:', filteredAmendments.length);

  if (loading) {
    console.log('Showing loading state');
    return (
      <div className="qa-dashboard" style={{ minHeight: '400px', padding: '40px' }}>
        <div style={{
          fontSize: '1.5rem',
          textAlign: 'center',
          padding: '40px',
          background: '#f3f4f6',
          borderRadius: '8px'
        }}>
          Loading QA Dashboard... (Check console for details)
          <div style={{ marginTop: '20px', fontSize: '1rem', color: '#6b7280' }}>
            If this stays visible, check browser console (F12) for errors
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    console.error('Showing error state:', error);
    return (
      <div className="qa-dashboard">
        <div className="error">{error}</div>
        <button onClick={() => window.location.reload()}>Reload Page</button>
      </div>
    );
  }

  console.log('Rendering main dashboard content');

  const groupedAmendments = groupByVersion ? groupAmendmentsByVersion() : null;

  return (
    <div className="qa-dashboard">
      <div className="qa-dashboard-header">
        <h1>QA Dashboard</h1>
        <p className="qa-dashboard-subtitle">Manage and track all QA assignments</p>
      </div>

      {/* Statistics Cards */}
      <div className="qa-stats-grid">
        <div className="qa-stat-card qa-stat-total">
          <div className="qa-stat-value">{stats.total}</div>
          <div className="qa-stat-label">Total Amendments</div>
        </div>
        <div className="qa-stat-card qa-stat-not-started">
          <div className="qa-stat-value">{stats.notStarted}</div>
          <div className="qa-stat-label">Not Started</div>
        </div>
        <div className="qa-stat-card qa-stat-in-testing">
          <div className="qa-stat-value">{stats.inTesting}</div>
          <div className="qa-stat-label">In Testing</div>
        </div>
        <div className="qa-stat-card qa-stat-blocked">
          <div className="qa-stat-value">{stats.blocked}</div>
          <div className="qa-stat-label">Blocked</div>
        </div>
        <div className="qa-stat-card qa-stat-passed">
          <div className="qa-stat-value">{stats.passed}</div>
          <div className="qa-stat-label">Passed</div>
        </div>
        <div className="qa-stat-card qa-stat-failed">
          <div className="qa-stat-value">{stats.failed}</div>
          <div className="qa-stat-label">Failed</div>
        </div>
      </div>

      {/* Filters Panel */}
      <div className="qa-filters-panel">
        <div className="qa-filters-header">
          <h3>Filters</h3>
          <button className="qa-clear-filters-btn" onClick={clearFilters}>
            Clear All
          </button>
        </div>

        <div className="qa-filters-grid">
          {/* Search */}
          <div className="qa-filter-item qa-filter-search">
            <label>Search</label>
            <input
              type="text"
              placeholder="Search by reference or description..."
              value={filters.searchText}
              onChange={(e) => handleFilterChange('searchText', e.target.value)}
              className="qa-filter-input"
            />
          </div>

          {/* Application Filter */}
          <div className="qa-filter-item">
            <label>Application</label>
            <select
              value={filters.application}
              onChange={(e) => handleFilterChange('application', e.target.value)}
              className="qa-filter-select"
            >
              <option value="all">All Applications</option>
              {applications.map((app) => (
                <option key={app.application_id} value={app.application_name}>
                  {app.application_name}
                </option>
              ))}
            </select>
          </div>

          {/* QA Assigned To Filter */}
          <div className="qa-filter-item">
            <label>Assigned To</label>
            <select
              value={filters.qaAssignedTo}
              onChange={(e) => handleFilterChange('qaAssignedTo', e.target.value)}
              className="qa-filter-select"
            >
              <option value="all">All Users</option>
              {employees
                .filter((e) => e.is_active)
                .map((emp) => (
                  <option key={emp.employee_id} value={emp.employee_id}>
                    {emp.employee_name}
                  </option>
                ))}
            </select>
          </div>

          {/* Version Filter */}
          <div className="qa-filter-item">
            <label>Version</label>
            <select
              value={filters.version}
              onChange={(e) => handleFilterChange('version', e.target.value)}
              className="qa-filter-select"
            >
              <option value="all">All Versions</option>
              {versions.map((version, idx) => (
                <option key={idx} value={version}>
                  {version}
                </option>
              ))}
            </select>
          </div>

          {/* QA Status Filter */}
          <div className="qa-filter-item">
            <label>QA Status</label>
            <select
              value={filters.qaStatus}
              onChange={(e) => handleFilterChange('qaStatus', e.target.value)}
              className="qa-filter-select"
            >
              <option value="all">All Statuses</option>
              <option value="Not Started">Not Started</option>
              <option value="Assigned">Assigned</option>
              <option value="In Testing">In Testing</option>
              <option value="Blocked">Blocked</option>
              <option value="Passed">Passed</option>
              <option value="Failed">Failed</option>
            </select>
          </div>

          {/* Overall Result Filter */}
          <div className="qa-filter-item">
            <label>Overall Result</label>
            <select
              value={filters.qaOverallResult}
              onChange={(e) => handleFilterChange('qaOverallResult', e.target.value)}
              className="qa-filter-select"
            >
              <option value="all">All Results</option>
              <option value="Passed">Passed</option>
              <option value="Failed">Failed</option>
              <option value="Passed with Issues">Passed with Issues</option>
            </select>
          </div>
        </div>

        {/* Quick Filters */}
        <div className="qa-quick-filters">
          <button
            className={`qa-quick-filter-btn ${showMyAssignments ? 'active' : ''}`}
            onClick={() => setShowMyAssignments(!showMyAssignments)}
          >
            👤 My Assignments
          </button>
          <button
            className={`qa-quick-filter-btn ${groupByVersion ? 'active' : ''}`}
            onClick={() => setGroupByVersion(!groupByVersion)}
          >
            📦 Group by Version
          </button>
        </div>
      </div>

      {/* Amendments List */}
      <div className="qa-amendments-section">
        <div className="qa-amendments-header">
          <h3>
            QA Assignments ({filteredAmendments.length})
          </h3>
        </div>

        {filteredAmendments.length === 0 ? (
          <div className="qa-empty-state">
            <div className="qa-empty-icon">🔍</div>
            <h3>No QA assignments found</h3>
            <p>Try adjusting your filters or create new amendments</p>
          </div>
        ) : groupByVersion ? (
          // Grouped by Version View
          <>
            <div className="qa-version-groups">
              {Object.entries(groupedAmendments).slice(0, displayLimit / 5).map(([version, versionAmendments]) => (
                <div key={version} className="qa-version-group">
                  <div className="qa-version-header">
                    <h4>
                      📦 {version} ({versionAmendments.length})
                    </h4>
                  </div>
                  <div className="qa-amendments-grid">
                    {versionAmendments.map((amendment) => (
                      <AmendmentCard
                        key={amendment.amendment_id}
                        amendment={amendment}
                        navigate={navigate}
                        getAssignedEmployeeName={getAssignedEmployeeName}
                        formatDate={formatDate}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
            {Object.entries(groupedAmendments).length > displayLimit / 5 && (
              <div style={{ textAlign: 'center', marginTop: '20px', marginBottom: '20px' }}>
                <button
                  onClick={() => setDisplayLimit(displayLimit + 25)}
                  className="btn btn-secondary"
                  style={{
                    padding: '10px 30px',
                    fontSize: '14px',
                    backgroundColor: '#6c757d',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Load More Versions
                </button>
              </div>
            )}
          </>
        ) : (
          // List View
          <>
            <div className="qa-amendments-grid">
              {filteredAmendments.slice(0, displayLimit).map((amendment) => (
                <AmendmentCard
                  key={amendment.amendment_id}
                  amendment={amendment}
                  navigate={navigate}
                  getAssignedEmployeeName={getAssignedEmployeeName}
                  formatDate={formatDate}
                />
              ))}
            </div>
            {filteredAmendments.length > displayLimit && (
              <div style={{ textAlign: 'center', marginTop: '20px', marginBottom: '20px' }}>
                <button
                  onClick={() => setDisplayLimit(displayLimit + 25)}
                  className="btn btn-secondary"
                  style={{
                    padding: '10px 30px',
                    fontSize: '14px',
                    backgroundColor: '#6c757d',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Load More ({filteredAmendments.length - displayLimit} remaining)
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

// Amendment Card Component
const AmendmentCard = ({ amendment, navigate, getAssignedEmployeeName, formatDate }) => {
  if (!amendment) return null;

  return (
    <div
      className="qa-amendment-card"
      onClick={() => navigate(`/amendments/${amendment.amendment_id}`)}
    >
      <div className="qa-amendment-card-header">
        <div className="qa-amendment-ref">{amendment.amendment_reference || 'N/A'}</div>
        <StatusBadge status={amendment.qa_status || 'Not Started'} showIcon={true} size="small" />
      </div>

      <div className="qa-amendment-description">
        {amendment.description?.substring(0, 100)}
        {amendment.description?.length > 100 && '...'}
      </div>

      <div className="qa-amendment-meta">
        {amendment.application && (
          <div className="qa-meta-item">
            <span className="qa-meta-label">App:</span>
            <span className="qa-meta-value">{amendment.application}</span>
          </div>
        )}
        {amendment.version && (
          <div className="qa-meta-item">
            <span className="qa-meta-label">Version:</span>
            <span className="qa-meta-value">{amendment.version}</span>
          </div>
        )}
      </div>

      <div className="qa-amendment-assignee">
        <div className="qa-assignee-avatar">
          {getAssignedEmployeeName(amendment.qa_assigned_id)
            .split(' ')
            .map((n) => n[0])
            .join('')}
        </div>
        <div className="qa-assignee-info">
          <div className="qa-assignee-name">
            {getAssignedEmployeeName(amendment.qa_assigned_id)}
          </div>
          {amendment.qa_assigned_date && (
            <div className="qa-assignee-date">
              Assigned: {formatDate(amendment.qa_assigned_date)}
            </div>
          )}
        </div>
      </div>

      {amendment.qa_overall_result && (
        <div className="qa-overall-result">
          <StatusBadge status={amendment.qa_overall_result} showIcon={true} size="small" />
        </div>
      )}

      <div className="qa-card-footer">
        <span className="qa-priority">{amendment.priority}</span>
        {amendment.qa_due_date && (
          <span className="qa-due-date">Due: {formatDate(amendment.qa_due_date)}</span>
        )}
      </div>
    </div>
  );
};

export default QADashboard;
