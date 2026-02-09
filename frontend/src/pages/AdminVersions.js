import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Admin.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

function AdminVersions() {
  const [versions, setVersions] = useState([]);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingVersion, setEditingVersion] = useState(null);
  const [formData, setFormData] = useState({
    application_id: '',
    version: '',
    released_date: '',
    notes: '',
    is_active: true,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [versionsRes, appsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/application-versions`),
        axios.get(`${API_BASE_URL}/applications`),
      ]);
      setVersions(versionsRes.data || []);
      setApplications(appsRes.data || []);
    } catch (error) {
      console.error('Error loading data:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingVersion(null);
    setFormData({
      application_id: applications.length > 0 ? applications[0].application_id : '',
      version: '',
      released_date: '',
      notes: '',
      is_active: true,
    });
    setShowModal(true);
  };

  const handleEdit = (version) => {
    setEditingVersion(version);
    setFormData({
      application_id: version.application_id,
      version: version.version,
      released_date: version.released_date ? version.released_date.split('T')[0] : '',
      notes: version.notes || '',
      is_active: version.is_active,
    });
    setShowModal(true);
  };

  const handleSave = async () => {
    try {
      if (!formData.application_id) {
        alert('Application is required');
        return;
      }
      if (!formData.version.trim()) {
        alert('Version is required');
        return;
      }

      const payload = {
        ...formData,
        released_date: formData.released_date || null,
      };

      if (editingVersion) {
        // Update existing
        await axios.put(`${API_BASE_URL}/application-versions/${editingVersion.application_version_id}`, payload);
      } else {
        // Create new
        await axios.post(`${API_BASE_URL}/application-versions`, payload);
      }

      setShowModal(false);
      loadData();
    } catch (error) {
      console.error('Error saving version:', error);
      alert(error.response?.data?.detail || 'Failed to save version');
    }
  };

  const handleDelete = async (version) => {
    const appName = applications.find(a => a.application_id === version.application_id)?.application_name || 'Unknown';
    if (!window.confirm(`Are you sure you want to delete "${appName} ${version.version}"?`)) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/application-versions/${version.application_version_id}`);
      loadData();
    } catch (error) {
      console.error('Error deleting version:', error);
      alert(error.response?.data?.detail || 'Failed to delete version');
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const getApplicationName = (appId) => {
    const app = applications.find(a => a.application_id === appId);
    return app ? app.application_name : 'Unknown';
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-GB');
  };

  if (loading) {
    return (
      <div className="admin-page">
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-3">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
            <div className="text-gray-500 dark:text-gray-400">Loading versions...</div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="admin-page">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 p-6 rounded-lg">
          <div className="flex items-start gap-3">
            <span className="material-symbols-outlined text-2xl">error</span>
            <div className="flex-1">
              <h3 className="font-semibold mb-1">Failed to load versions</h3>
              <p className="text-sm mb-3">{error}</p>
              <button
                onClick={loadData}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h2>Application Versions</h2>
        <button className="btn btn-primary" onClick={handleAdd}>
          + Add Version
        </button>
      </div>

      {versions.length === 0 ? (
        <div className="admin-empty-state">
          <p>No versions found</p>
          <button className="btn btn-primary" onClick={handleAdd}>
            Add Your First Version
          </button>
        </div>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Application</th>
              <th>Version</th>
              <th>Released Date</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {versions.map((version) => (
              <tr key={version.application_version_id}>
                <td>{version.application_version_id}</td>
                <td>{getApplicationName(version.application_id)}</td>
                <td>{version.version}</td>
                <td>{formatDate(version.released_date)}</td>
                <td>
                  <span style={{ color: version.is_active ? '#28a745' : '#6c757d' }}>
                    {version.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>
                  <div className="admin-actions">
                    <button className="btn-edit" onClick={() => handleEdit(version)}>
                      Edit
                    </button>
                    <button className="btn-delete" onClick={() => handleDelete(version)}>
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {showModal && (
        <div className="admin-modal" onClick={() => setShowModal(false)}>
          <div className="admin-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3>{editingVersion ? 'Edit Version' : 'Add Version'}</h3>
              <button className="admin-modal-close" onClick={() => setShowModal(false)}>
                &times;
              </button>
            </div>

            <div className="admin-form-group">
              <label>Application *</label>
              <select
                name="application_id"
                value={formData.application_id}
                onChange={handleChange}
              >
                <option value="">Select Application</option>
                {applications.map((app) => (
                  <option key={app.application_id} value={app.application_id}>
                    {app.application_name}
                  </option>
                ))}
              </select>
            </div>

            <div className="admin-form-group">
              <label>Version *</label>
              <input
                type="text"
                name="version"
                value={formData.version}
                onChange={handleChange}
                placeholder="e.g., 7.5.0"
              />
            </div>

            <div className="admin-form-group">
              <label>Released Date</label>
              <input
                type="date"
                name="released_date"
                value={formData.released_date}
                onChange={handleChange}
              />
            </div>

            <div className="admin-form-group">
              <label>Notes</label>
              <textarea
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                placeholder="Optional release notes"
              />
            </div>

            <div className="admin-form-group">
              <div className="checkbox-group">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleChange}
                  id="is_active_version"
                />
                <label htmlFor="is_active_version">Active</label>
              </div>
            </div>

            <div className="admin-form-actions">
              <button className="btn-secondary" onClick={() => setShowModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleSave}>
                {editingVersion ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminVersions;
