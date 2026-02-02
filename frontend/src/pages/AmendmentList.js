import React, { useState, useEffect, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { amendmentAPI, referenceAPI } from '../services/api';
import './AmendmentList.css';

function AmendmentList() {
  const location = useLocation();

  // Parse URL query parameters on mount
  const getInitialFilters = () => {
    const searchParams = new URLSearchParams(location.search);

    // Helper to parse boolean params
    const parseBoolParam = (value) => {
      if (value === 'true') return true;
      if (value === 'false') return false;
      return '';
    };

    return {
      search_text: searchParams.get('search_text') || '',
      amendment_status: searchParams.get('amendment_status') || '',
      priority: searchParams.get('priority') || '',
      amendment_type: searchParams.get('amendment_type') || '',
      force: searchParams.get('force') || '',
      application: searchParams.get('application') || '',
      development_status: searchParams.get('development_status') || '',
      assigned_to: searchParams.get('assigned_to') || '',
      reported_by: searchParams.get('reported_by') || '',
      qa_completed: parseBoolParam(searchParams.get('qa_completed')),
      database_changes: parseBoolParam(searchParams.get('database_changes')),
      db_upgrade_changes: parseBoolParam(searchParams.get('db_upgrade_changes')),
    };
  };

  const [amendments, setAmendments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [statuses, setStatuses] = useState([]);
  const [priorities, setPriorities] = useState([]);
  const [types, setTypes] = useState([]);
  const [developmentStatuses, setDevelopmentStatuses] = useState([]);

  const [filters, setFilters] = useState(getInitialFilters());

  const [pagination, setPagination] = useState({
    skip: 0,
    limit: 25,
  });

  const loadReferenceData = useCallback(async () => {
    try {
      const [statusRes, priorityRes, typeRes, devStatusRes] = await Promise.all([
        referenceAPI.getStatuses(),
        referenceAPI.getPriorities(),
        referenceAPI.getTypes(),
        referenceAPI.getDevelopmentStatuses(),
      ]);
      setStatuses(statusRes.data);
      setPriorities(priorityRes.data);
      setTypes(typeRes.data);
      setDevelopmentStatuses(devStatusRes.data);
    } catch (err) {
      console.error('Failed to load reference data:', err);
    }
  }, []);

  const loadAmendments = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        ...pagination,
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, value]) => value !== '')
        ),
      };
      const response = await amendmentAPI.getAll(params);
      // Extract items array from response
      setAmendments(response.data.items || []);
      setError(null);
    } catch (err) {
      setError('Failed to load amendments: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  }, [filters, pagination]);

  useEffect(() => {
    loadReferenceData();
  }, [loadReferenceData]);

  useEffect(() => {
    loadAmendments();
  }, [loadAmendments]);

  // Update filters when URL changes
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);

    // Helper to parse boolean params
    const parseBoolParam = (value) => {
      if (value === 'true') return true;
      if (value === 'false') return false;
      return '';
    };

    setFilters({
      search_text: searchParams.get('search_text') || '',
      amendment_status: searchParams.get('amendment_status') || '',
      priority: searchParams.get('priority') || '',
      amendment_type: searchParams.get('amendment_type') || '',
      force: searchParams.get('force') || '',
      development_status: searchParams.get('development_status') || '',
      assigned_to: searchParams.get('assigned_to') || '',
      reported_by: searchParams.get('reported_by') || '',
      qa_completed: parseBoolParam(searchParams.get('qa_completed')),
      database_changes: parseBoolParam(searchParams.get('database_changes')),
      db_upgrade_changes: parseBoolParam(searchParams.get('db_upgrade_changes')),
    });
    setPagination({ skip: 0, limit: 25 });
  }, [location.search]);

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value,
    }));
    setPagination(prev => ({ ...prev, skip: 0 }));
  };

  const clearFilters = () => {
    setFilters({
      search_text: '',
      amendment_status: '',
      priority: '',
      amendment_type: '',
      force: '',
      development_status: '',
      assigned_to: '',
      reported_by: '',
      qa_completed: '',
      database_changes: '',
      db_upgrade_changes: '',
    });
    setPagination({ skip: 0, limit: 25 });
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const getPriorityClass = (priority) => {
    return `priority-${priority.toLowerCase()}`;
  };

  const getStatusClass = (status) => {
    return `status-${status.toLowerCase().replace(' ', '-')}`;
  };

  return (
    <div className="amendment-list">
      <div className="page-header">
        <div>
          <h1 className="page-title">Amendments</h1>
          <p className="page-subtitle">Browse and search all amendments</p>
        </div>
        <Link to="/amendments/new" className="btn btn-primary">
          + New Amendment
        </Link>
      </div>

      <div className="filters-panel">
        <div className="filters-row">
          <input
            type="text"
            placeholder="Search description, notes..."
            value={filters.search_text}
            onChange={(e) => handleFilterChange('search_text', e.target.value)}
            className="filter-input search-input"
          />

          <select
            value={filters.amendment_status}
            onChange={(e) => handleFilterChange('amendment_status', e.target.value)}
            className="filter-select"
          >
            <option value="">All Statuses</option>
            {statuses.map(status => (
              <option key={status} value={status}>{status}</option>
            ))}
          </select>

          <select
            value={filters.priority}
            onChange={(e) => handleFilterChange('priority', e.target.value)}
            className="filter-select"
          >
            <option value="">All Priorities</option>
            {priorities.map(priority => (
              <option key={priority} value={priority}>{priority}</option>
            ))}
          </select>

          <select
            value={filters.amendment_type}
            onChange={(e) => handleFilterChange('amendment_type', e.target.value)}
            className="filter-select"
          >
            <option value="">All Types</option>
            {types.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>

          <select
            value={filters.development_status}
            onChange={(e) => handleFilterChange('development_status', e.target.value)}
            className="filter-select"
          >
            <option value="">All Dev Statuses</option>
            {developmentStatuses.map(status => (
              <option key={status} value={status}>{status}</option>
            ))}
          </select>

          <button onClick={clearFilters} className="btn btn-clear">
            Clear Filters
          </button>
        </div>
      </div>

      {loading && <div className="loading">Loading amendments...</div>}
      {error && <div className="error">{error}</div>}

      {!loading && !error && (
        <>
          <div className="results-info">
            Showing {amendments.length} amendments
          </div>

          <div className="amendments-table-container">
            <table className="amendments-table">
              <thead>
                <tr>
                  <th>Reference</th>
                  <th>Description</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>Assigned To</th>
                  <th>Date Reported</th>
                  <th>QA</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {amendments.length === 0 ? (
                  <tr>
                    <td colSpan="9" className="no-results">
                      No amendments found
                    </td>
                  </tr>
                ) : (
                  amendments.map(amendment => (
                    <tr key={amendment.amendment_id}>
                      <td>
                        <Link
                          to={`/amendments/${amendment.amendment_id}`}
                          className="amendment-reference"
                        >
                          {amendment.amendment_reference}
                        </Link>
                      </td>
                      <td className="description-cell">
                        {amendment.description.substring(0, 80)}
                        {amendment.description.length > 80 ? '...' : ''}
                      </td>
                      <td>
                        <span className="type-badge">
                          {amendment.amendment_type}
                        </span>
                      </td>
                      <td>
                        <span className={`status-badge ${getStatusClass(amendment.amendment_status)}`}>
                          {amendment.amendment_status}
                        </span>
                      </td>
                      <td>
                        <span className={`priority-badge ${getPriorityClass(amendment.priority)}`}>
                          {amendment.priority}
                        </span>
                      </td>
                      <td>{amendment.assigned_to || '-'}</td>
                      <td>{formatDate(amendment.date_reported)}</td>
                      <td className="qa-cell">
                        {amendment.qa_completed ? (
                          <span className="qa-badge qa-completed">✓</span>
                        ) : amendment.qa_assigned_id ? (
                          <span className="qa-badge qa-assigned">Assigned</span>
                        ) : (
                          <span className="qa-badge qa-none">-</span>
                        )}
                      </td>
                      <td>
                        <Link
                          to={`/amendments/${amendment.amendment_id}`}
                          className="btn-view"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <button
              onClick={() => setPagination(prev => ({
                ...prev,
                skip: Math.max(0, prev.skip - prev.limit)
              }))}
              disabled={pagination.skip === 0}
              className="btn btn-pagination"
            >
              Previous
            </button>
            <span className="pagination-info">
              Showing {pagination.skip + 1} - {pagination.skip + amendments.length}
            </span>
            <button
              onClick={() => setPagination(prev => ({
                ...prev,
                skip: prev.skip + prev.limit
              }))}
              disabled={amendments.length < pagination.limit}
              className="btn btn-pagination"
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default AmendmentList;
