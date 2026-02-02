import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Admin.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

function AdminEmployees() {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [formData, setFormData] = useState({
    employee_name: '',
    initials: '',
    email: '',
    windows_login: '',
    is_active: true,
  });

  useEffect(() => {
    loadEmployees();
  }, []);

  const loadEmployees = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/employees`);
      setEmployees(response.data || []);
    } catch (error) {
      console.error('Error loading employees:', error);
      alert('Failed to load employees');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingEmployee(null);
    setFormData({
      employee_name: '',
      initials: '',
      email: '',
      windows_login: '',
      is_active: true,
    });
    setShowModal(true);
  };

  const handleEdit = (employee) => {
    setEditingEmployee(employee);
    setFormData({
      employee_name: employee.employee_name,
      initials: employee.initials || '',
      email: employee.email || '',
      windows_login: employee.windows_login || '',
      is_active: employee.is_active,
    });
    setShowModal(true);
  };

  const handleSave = async () => {
    try {
      if (!formData.employee_name.trim()) {
        alert('Employee name is required');
        return;
      }

      if (editingEmployee) {
        // Update existing
        await axios.put(`${API_BASE_URL}/employees/${editingEmployee.employee_id}`, formData);
      } else {
        // Create new
        await axios.post(`${API_BASE_URL}/employees`, formData);
      }

      setShowModal(false);
      loadEmployees();
    } catch (error) {
      console.error('Error saving employee:', error);
      alert(error.response?.data?.detail || 'Failed to save employee');
    }
  };

  const handleDelete = async (employee) => {
    if (!window.confirm(`Are you sure you want to delete "${employee.employee_name}"?`)) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/employees/${employee.employee_id}`);
      loadEmployees();
    } catch (error) {
      console.error('Error deleting employee:', error);
      alert(error.response?.data?.detail || 'Failed to delete employee');
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
        <div className="admin-loading">Loading employees...</div>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h2>Employees</h2>
        <button className="btn btn-primary" onClick={handleAdd}>
          + Add Employee
        </button>
      </div>

      {employees.length === 0 ? (
        <div className="admin-empty-state">
          <p>No employees found</p>
          <button className="btn btn-primary" onClick={handleAdd}>
            Add Your First Employee
          </button>
        </div>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Initials</th>
              <th>Email</th>
              <th>Windows Login</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {employees.map((employee) => (
              <tr key={employee.employee_id}>
                <td>{employee.employee_id}</td>
                <td>{employee.employee_name}</td>
                <td>{employee.initials || '-'}</td>
                <td>{employee.email || '-'}</td>
                <td>{employee.windows_login || '-'}</td>
                <td>
                  <span style={{ color: employee.is_active ? '#28a745' : '#6c757d' }}>
                    {employee.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>
                  <div className="admin-actions">
                    <button className="btn-edit" onClick={() => handleEdit(employee)}>
                      Edit
                    </button>
                    <button className="btn-delete" onClick={() => handleDelete(employee)}>
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
              <h3>{editingEmployee ? 'Edit Employee' : 'Add Employee'}</h3>
              <button className="admin-modal-close" onClick={() => setShowModal(false)}>
                &times;
              </button>
            </div>

            <div className="admin-form-group">
              <label>Employee Name *</label>
              <input
                type="text"
                name="employee_name"
                value={formData.employee_name}
                onChange={handleChange}
                placeholder="e.g., John Smith"
              />
            </div>

            <div className="admin-form-group">
              <label>Initials</label>
              <input
                type="text"
                name="initials"
                value={formData.initials}
                onChange={handleChange}
                placeholder="e.g., JS"
              />
            </div>

            <div className="admin-form-group">
              <label>Email</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="e.g., john.smith@company.com"
              />
            </div>

            <div className="admin-form-group">
              <label>Windows Login</label>
              <input
                type="text"
                name="windows_login"
                value={formData.windows_login}
                onChange={handleChange}
                placeholder="e.g., DOMAIN\\jsmith"
              />
            </div>

            <div className="admin-form-group">
              <div className="checkbox-group">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleChange}
                  id="is_active_employee"
                />
                <label htmlFor="is_active_employee">Active</label>
              </div>
            </div>

            <div className="admin-form-actions">
              <button className="btn-secondary" onClick={() => setShowModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleSave}>
                {editingEmployee ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminEmployees;
