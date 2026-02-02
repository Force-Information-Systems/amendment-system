import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Admin.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

function AdminReference() {
  const [activeTab, setActiveTab] = useState('forces');
  const [forces, setForces] = useState([]);
  const [priorities, setPriorities] = useState([]);
  const [amendmentStatuses, setAmendmentStatuses] = useState([]);
  const [developmentStatuses, setDevelopmentStatuses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    is_active: true,
    sort_order: 0,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [forcesRes, prioritiesRes, statusesRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/forces`),
        axios.get(`${API_BASE_URL}/priorities`),
        axios.get(`${API_BASE_URL}/statuses`),
      ]);
      setForces(forcesRes.data || []);
      setPriorities(prioritiesRes.data || []);

      const statuses = statusesRes.data || [];
      setAmendmentStatuses(statuses.filter(s => s.status_type === 'amendment'));
      setDevelopmentStatuses(statuses.filter(s => s.status_type === 'development'));
    } catch (error) {
      console.error('Error loading reference data:', error);
      alert('Failed to load reference data');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingItem(null);
    setFormData({
      name: '',
      is_active: true,
      sort_order: getNextSortOrder(),
    });
    setShowModal(true);
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setFormData({
      name: getItemName(item),
      is_active: item.is_active,
      sort_order: item.sort_order,
    });
    setShowModal(true);
  };

  const getItemName = (item) => {
    if (item.force_name) return item.force_name;
    if (item.priority_name) return item.priority_name;
    if (item.status_name) return item.status_name;
    return '';
  };

  const getItemId = (item) => {
    if (item.force_id) return item.force_id;
    if (item.priority_id) return item.priority_id;
    if (item.status_id) return item.status_id;
    return null;
  };

  const getNextSortOrder = () => {
    let items = [];
    if (activeTab === 'forces') items = forces;
    else if (activeTab === 'priorities') items = priorities;
    else if (activeTab === 'amendment-statuses') items = amendmentStatuses;
    else if (activeTab === 'development-statuses') items = developmentStatuses;

    if (items.length === 0) return 1;
    return Math.max(...items.map(i => i.sort_order || 0)) + 1;
  };

  const handleSave = async () => {
    try {
      if (!formData.name.trim()) {
        alert('Name is required');
        return;
      }

      let endpoint = '';
      let payload = {};

      if (activeTab === 'forces') {
        endpoint = editingItem ? `/forces/${getItemId(editingItem)}` : '/forces';
        payload = {
          force_name: formData.name,
          is_active: formData.is_active,
          sort_order: formData.sort_order,
        };
      } else if (activeTab === 'priorities') {
        endpoint = editingItem ? `/priorities/${getItemId(editingItem)}` : '/priorities';
        payload = {
          priority_name: formData.name,
          is_active: formData.is_active,
          sort_order: formData.sort_order,
        };
      } else if (activeTab === 'amendment-statuses' || activeTab === 'development-statuses') {
        const statusType = activeTab === 'amendment-statuses' ? 'amendment' : 'development';
        endpoint = editingItem ? `/statuses/${getItemId(editingItem)}` : '/statuses';
        payload = {
          status_name: formData.name,
          status_type: statusType,
          is_active: formData.is_active,
          sort_order: formData.sort_order,
        };
      }

      if (editingItem) {
        await axios.put(`${API_BASE_URL}${endpoint}`, null, { params: payload });
      } else {
        await axios.post(`${API_BASE_URL}${endpoint}`, null, { params: payload });
      }

      setShowModal(false);
      loadData();
    } catch (error) {
      console.error('Error saving item:', error);
      alert(error.response?.data?.detail || 'Failed to save item');
    }
  };

  const handleDelete = async (item) => {
    if (!window.confirm(`Are you sure you want to delete "${getItemName(item)}"?`)) {
      return;
    }

    try {
      let endpoint = '';
      if (activeTab === 'forces') {
        endpoint = `/forces/${getItemId(item)}`;
      } else if (activeTab === 'priorities') {
        endpoint = `/priorities/${getItemId(item)}`;
      } else {
        endpoint = `/statuses/${getItemId(item)}`;
      }

      await axios.delete(`${API_BASE_URL}${endpoint}`);
      loadData();
    } catch (error) {
      console.error('Error deleting item:', error);
      alert(error.response?.data?.detail || 'Failed to delete item');
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const renderTable = (items, title) => {
    return (
      <div>
        <div className="admin-page-header">
          <h2>{title}</h2>
          <button className="btn btn-primary" onClick={handleAdd}>
            + Add {title.slice(0, -1)}
          </button>
        </div>

        {items.length === 0 ? (
          <div className="admin-empty-state">
            <p>No {title.toLowerCase()} found</p>
          </div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Sort Order</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={getItemId(item)}>
                  <td>{getItemId(item)}</td>
                  <td>{getItemName(item)}</td>
                  <td>{item.sort_order}</td>
                  <td>
                    <span style={{ color: item.is_active ? '#28a745' : '#6c757d' }}>
                      {item.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <div className="admin-actions">
                      <button className="btn-edit" onClick={() => handleEdit(item)}>
                        Edit
                      </button>
                      <button className="btn-delete" onClick={() => handleDelete(item)}>
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="admin-page">
        <div className="admin-loading">Loading reference data...</div>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <div className="admin-page-header" style={{ borderBottom: 'none', paddingBottom: 0 }}>
        <div>
          <h2>Reference Data Management</h2>
          <p style={{ margin: '8px 0 0 0', color: '#6c757d', fontSize: '0.9em' }}>
            Manage dropdown values for the amendment system
          </p>
        </div>
      </div>

      <div className="admin-tabs" style={{ marginTop: '20px' }}>
        <button
          className={`admin-tab ${activeTab === 'forces' ? 'active' : ''}`}
          onClick={() => setActiveTab('forces')}
        >
          Forces ({forces.length})
        </button>
        <button
          className={`admin-tab ${activeTab === 'priorities' ? 'active' : ''}`}
          onClick={() => setActiveTab('priorities')}
        >
          Priorities ({priorities.length})
        </button>
        <button
          className={`admin-tab ${activeTab === 'amendment-statuses' ? 'active' : ''}`}
          onClick={() => setActiveTab('amendment-statuses')}
        >
          Amendment Statuses ({amendmentStatuses.length})
        </button>
        <button
          className={`admin-tab ${activeTab === 'development-statuses' ? 'active' : ''}`}
          onClick={() => setActiveTab('development-statuses')}
        >
          Development Statuses ({developmentStatuses.length})
        </button>
      </div>

      <div className="admin-tab-content">
        {activeTab === 'forces' && renderTable(forces, 'Forces')}
        {activeTab === 'priorities' && renderTable(priorities, 'Priorities')}
        {activeTab === 'amendment-statuses' && renderTable(amendmentStatuses, 'Amendment Statuses')}
        {activeTab === 'development-statuses' && renderTable(developmentStatuses, 'Development Statuses')}
      </div>

      {showModal && (
        <div className="admin-modal" onClick={() => setShowModal(false)}>
          <div className="admin-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h3>{editingItem ? 'Edit Item' : 'Add Item'}</h3>
              <button className="admin-modal-close" onClick={() => setShowModal(false)}>
                &times;
              </button>
            </div>

            <div className="admin-form-group">
              <label>Name *</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="Enter name"
              />
            </div>

            <div className="admin-form-group">
              <label>Sort Order</label>
              <input
                type="number"
                name="sort_order"
                value={formData.sort_order}
                onChange={handleChange}
                placeholder="0"
              />
            </div>

            <div className="admin-form-group">
              <div className="checkbox-group">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleChange}
                  id="is_active_ref"
                />
                <label htmlFor="is_active_ref">Active</label>
              </div>
            </div>

            <div className="admin-form-actions">
              <button className="btn-secondary" onClick={() => setShowModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleSave}>
                {editingItem ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminReference;
