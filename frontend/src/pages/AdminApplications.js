import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Admin.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

function AdminApplications() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingApp, setEditingApp] = useState(null);
  const [formData, setFormData] = useState({
    application_name: '',
    description: '',
    is_active: true,
  });

  useEffect(() => {
    loadApplications();
  }, []);

  const loadApplications = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE_URL}/applications`);
      setApplications(response.data || []);
    } catch (error) {
      console.error('Error loading applications:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to load applications');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingApp(null);
    setFormData({
      application_name: '',
      description: '',
      is_active: true,
    });
    setShowModal(true);
  };

  const handleEdit = (app) => {
    setEditingApp(app);
    setFormData({
      application_name: app.application_name,
      description: app.description || '',
      is_active: app.is_active,
    });
    setShowModal(true);
  };

  const handleSave = async () => {
    try {
      if (!formData.application_name.trim()) {
        alert('Application name is required');
        return;
      }

      if (editingApp) {
        // Update existing
        await axios.put(`${API_BASE_URL}/applications/${editingApp.application_id}`, formData);
      } else {
        // Create new
        await axios.post(`${API_BASE_URL}/applications`, formData);
      }

      setShowModal(false);
      loadApplications();
    } catch (error) {
      console.error('Error saving application:', error);
      alert(error.response?.data?.detail || 'Failed to save application');
    }
  };

  const handleDelete = async (app) => {
    if (!window.confirm(`Are you sure you want to delete "${app.application_name}"? This will also delete all associated versions.`)) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/applications/${app.application_id}`);
      loadApplications();
    } catch (error) {
      console.error('Error deleting application:', error);
      alert(error.response?.data?.detail || 'Failed to delete application');
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  if (loading) {
    return (
      <div className="admin-page">
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-3">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
            <div className="text-gray-500 dark:text-gray-400">Loading applications...</div>
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
              <h3 className="font-semibold mb-1">Failed to load applications</h3>
              <p className="text-sm mb-3">{error}</p>
              <button
                onClick={loadApplications}
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
        <h2>Applications</h2>
        <button className="btn btn-primary" onClick={handleAdd}>
          + Add Application
        </button>
      </div>

      {applications.length === 0 ? (
        <div className="admin-empty-state">
          <p>No applications found</p>
          <button className="btn btn-primary" onClick={handleAdd}>
            Add Your First Application
          </button>
        </div>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Application Name</th>
              <th>Description</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {applications.map((app) => (
              <tr key={app.application_id}>
                <td>{app.application_id}</td>
                <td>{app.application_name}</td>
                <td>{app.description || '-'}</td>
                <td>
                  <span style={{ color: app.is_active ? '#28a745' : '#6c757d' }}>
                    {app.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>
                  <div className="admin-actions">
                    <button className="btn-edit" onClick={() => handleEdit(app)}>
                      Edit
                    </button>
                    <button className="btn-delete" onClick={() => handleDelete(app)}>
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
              <h3>{editingApp ? 'Edit Application' : 'Add Application'}</h3>
              <button className="admin-modal-close" onClick={() => setShowModal(false)}>
                &times;
              </button>
            </div>

            <div className="admin-form-group">
              <label>Application Name *</label>
              <input
                type="text"
                name="application_name"
                value={formData.application_name}
                onChange={handleChange}
                placeholder="e.g., Centurion English"
              />
            </div>

            <div className="admin-form-group">
              <label>Description</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="Optional description"
              />
            </div>

            <div className="admin-form-group">
              <div className="checkbox-group">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleChange}
                  id="is_active"
                />
                <label htmlFor="is_active">Active</label>
              </div>
            </div>

            <div className="admin-form-actions">
              <button className="btn-secondary" onClick={() => setShowModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleSave}>
                {editingApp ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminApplications;
