import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { amendmentAPI, referenceAPI, employeeAPI, documentAPI } from '../services/api';
import QASection from '../components/QASection';
import './AmendmentDetail.css';

function AmendmentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [amendment, setAmendment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({});
  const [saving, setSaving] = useState(false);

  // Reference data
  const [types, setTypes] = useState([]);
  const [statuses, setStatuses] = useState([]);
  const [devStatuses, setDevStatuses] = useState([]);
  const [priorities, setPriorities] = useState([]);
  const [forces, setForces] = useState([]);
  const [employees, setEmployees] = useState([]);

  // Progress modal
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [progressData, setProgressData] = useState({
    description: '',
    notes: '',
    start_date: new Date().toISOString().slice(0, 16)
  });

  // Document upload
  const [showDocumentModal, setShowDocumentModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [documentData, setDocumentData] = useState({
    document_name: '',
    document_type: 'Other',
    description: ''
  });
  const [uploading, setUploading] = useState(false);

  const loadAmendment = useCallback(async () => {
    try {
      setLoading(true);
      const response = await amendmentAPI.getById(id);
      setAmendment(response.data);
      setFormData(response.data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load amendment');
    } finally {
      setLoading(false);
    }
  }, [id]);

  const loadReferenceData = useCallback(async () => {
    try {
      const [typesRes, statusesRes, devStatusesRes, prioritiesRes, forcesRes, employeesRes] = await Promise.all([
        referenceAPI.getTypes(),
        referenceAPI.getStatuses(),
        referenceAPI.getDevelopmentStatuses(),
        referenceAPI.getPriorities(),
        referenceAPI.getForces(),
        employeeAPI.getAll({ active_only: true }),
      ]);

      setTypes(typesRes.data);
      setStatuses(statusesRes.data);
      setDevStatuses(devStatusesRes.data);
      setPriorities(prioritiesRes.data);
      setForces(forcesRes.data);
      setEmployees(employeesRes.data);
    } catch (err) {
      console.error('Failed to load reference data:', err);
    }
  }, []);

  useEffect(() => {
    loadAmendment();
    loadReferenceData();
  }, [loadAmendment, loadReferenceData]);

  const handleEdit = () => {
    setEditing(true);
  };

  const handleCancel = () => {
    setEditing(false);
    setFormData(amendment);
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await amendmentAPI.update(id, formData);
      await loadAmendment();
      setEditing(false);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save amendment');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this amendment?')) {
      try {
        await amendmentAPI.delete(id);
        navigate('/amendments');
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to delete amendment');
      }
    }
  };

  const handleAddProgress = async () => {
    try {
      await amendmentAPI.addProgress(id, progressData);
      setShowProgressModal(false);
      setProgressData({
        description: '',
        notes: '',
        start_date: new Date().toISOString().slice(0, 16)
      });
      await loadAmendment();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add progress');
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setUploadFile(file);
      if (!documentData.document_name) {
        setDocumentData(prev => ({
          ...prev,
          document_name: file.name
        }));
      }
    }
  };

  const handleUploadDocument = async () => {
    if (!uploadFile) {
      setError('Please select a file to upload');
      return;
    }

    if (!documentData.document_name) {
      setError('Please enter a document name');
      return;
    }

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('document_name', documentData.document_name);
      formData.append('document_type', documentData.document_type);
      if (documentData.description) {
        formData.append('description', documentData.description);
      }

      await documentAPI.upload(id, formData);
      setShowDocumentModal(false);
      setUploadFile(null);
      setDocumentData({
        document_name: '',
        document_type: 'Other',
        description: ''
      });
      await loadAmendment();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const handleDownloadDocument = async (documentId, filename) => {
    try {
      const response = await documentAPI.download(documentId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to download document');
    }
  };

  const handleDeleteDocument = async (documentId) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await documentAPI.delete(documentId);
        await loadAmendment();
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to delete document');
      }
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return <div className="loading">Loading amendment...</div>;
  }

  if (error && !amendment) {
    return (
      <div className="error-container">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={() => navigate('/amendments')}>Back to List</button>
      </div>
    );
  }

  return (
    <div className="amendment-detail">
      <div className="detail-header">
        <div>
          <h1>{amendment.amendment_reference}</h1>
          <div className="status-badges">
            <span className={`badge status-${amendment.amendment_status.toLowerCase().replace(' ', '-')}`}>
              {amendment.amendment_status}
            </span>
            <span className={`badge dev-status-${amendment.development_status.toLowerCase().replace(' ', '-')}`}>
              {amendment.development_status}
            </span>
            <span className={`badge priority-${amendment.priority.toLowerCase()}`}>
              {amendment.priority}
            </span>
          </div>
        </div>
        <div className="detail-actions">
          {!editing ? (
            <>
              <button className="btn btn-primary" onClick={handleEdit}>Edit</button>
              <button className="btn btn-success" onClick={() => setShowProgressModal(true)}>Add Progress</button>
              <button className="btn btn-info" onClick={() => setShowDocumentModal(true)}>Upload Document</button>
              <button className="btn btn-danger" onClick={handleDelete}>Delete</button>
            </>
          ) : (
            <>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button className="btn btn-secondary" onClick={handleCancel}>Cancel</button>
              <button className="btn btn-success" onClick={() => setShowProgressModal(true)}>Add Progress</button>
              <button className="btn btn-info" onClick={() => setShowDocumentModal(true)}>Upload Document</button>
            </>
          )}
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="detail-content">
        <div className="detail-section">
          <h2>Details</h2>
          <div className="detail-grid">
            <div className="detail-field">
              <label>Type</label>
              {editing ? (
                <select name="amendment_type" value={formData.amendment_type} onChange={handleChange}>
                  {types.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              ) : (
                <div>{amendment.amendment_type}</div>
              )}
            </div>

            <div className="detail-field">
              <label>Status</label>
              {editing ? (
                <select name="amendment_status" value={formData.amendment_status} onChange={handleChange}>
                  {statuses.map(status => (
                    <option key={status} value={status}>{status}</option>
                  ))}
                </select>
              ) : (
                <div>{amendment.amendment_status}</div>
              )}
            </div>

            <div className="detail-field">
              <label>Development Status</label>
              {editing ? (
                <select name="development_status" value={formData.development_status} onChange={handleChange}>
                  {devStatuses.map(status => (
                    <option key={status} value={status}>{status}</option>
                  ))}
                </select>
              ) : (
                <div>{amendment.development_status}</div>
              )}
            </div>

            <div className="detail-field">
              <label>Priority</label>
              {editing ? (
                <select name="priority" value={formData.priority} onChange={handleChange}>
                  {priorities.map(priority => (
                    <option key={priority} value={priority}>{priority}</option>
                  ))}
                </select>
              ) : (
                <div>{amendment.priority}</div>
              )}
            </div>

            <div className="detail-field">
              <label>Force</label>
              {editing ? (
                <select name="force" value={formData.force || ''} onChange={handleChange}>
                  <option value="">None</option>
                  {forces.map(force => (
                    <option key={force} value={force}>{force}</option>
                  ))}
                </select>
              ) : (
                <div>{amendment.force || 'N/A'}</div>
              )}
            </div>

            <div className="detail-field">
              <label>Application</label>
              {editing ? (
                <input
                  type="text"
                  name="application"
                  value={formData.application || ''}
                  onChange={handleChange}
                />
              ) : (
                <div>{amendment.application || 'N/A'}</div>
              )}
            </div>

            <div className="detail-field">
              <label>Reported By</label>
              {editing ? (
                <select
                  name="reported_by"
                  value={formData.reported_by || ''}
                  onChange={handleChange}
                >
                  <option value="">Select Reporter</option>
                  {employees.map(emp => (
                    <option key={emp.employee_id} value={emp.initials}>
                      {emp.employee_name} ({emp.initials})
                    </option>
                  ))}
                </select>
              ) : (
                <div>{amendment.reported_by || 'N/A'}</div>
              )}
            </div>

            <div className="detail-field">
              <label>Assigned To</label>
              {editing ? (
                <select
                  name="assigned_to"
                  value={formData.assigned_to || ''}
                  onChange={handleChange}
                >
                  <option value="">Select Assignee</option>
                  {employees.map(emp => (
                    <option key={emp.employee_id} value={emp.initials}>
                      {emp.employee_name} ({emp.initials})
                    </option>
                  ))}
                </select>
              ) : (
                <div>{amendment.assigned_to || 'N/A'}</div>
              )}
            </div>

            <div className="detail-field">
              <label>Date Reported</label>
              {editing ? (
                <input
                  type="datetime-local"
                  name="date_reported"
                  value={formData.date_reported ? new Date(formData.date_reported).toISOString().slice(0, 16) : ''}
                  onChange={handleChange}
                />
              ) : (
                <div>{formatDate(amendment.date_reported)}</div>
              )}
            </div>
          </div>

          <div className="detail-field full-width">
            <label>Description</label>
            {editing ? (
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows="4"
              />
            ) : (
              <div className="text-content">{amendment.description}</div>
            )}
          </div>

          <div className="detail-field full-width">
            <label>Notes</label>
            {editing ? (
              <textarea
                name="notes"
                value={formData.notes || ''}
                onChange={handleChange}
                rows="4"
              />
            ) : (
              <div className="text-content">{amendment.notes || 'N/A'}</div>
            )}
          </div>

          <div className="detail-field full-width">
            <label>Release Notes</label>
            {editing ? (
              <textarea
                name="release_notes"
                value={formData.release_notes || ''}
                onChange={handleChange}
                rows="4"
              />
            ) : (
              <div className="text-content">{amendment.release_notes || 'N/A'}</div>
            )}
          </div>

          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                name="database_changes"
                checked={editing ? formData.database_changes : amendment.database_changes}
                onChange={handleChange}
                disabled={!editing}
              />
              Database Changes
            </label>
            <label>
              <input
                type="checkbox"
                name="db_upgrade_changes"
                checked={editing ? formData.db_upgrade_changes : amendment.db_upgrade_changes}
                onChange={handleChange}
                disabled={!editing}
              />
              DB Upgrade Changes
            </label>
          </div>
        </div>

        <QASection
          amendment={amendment}
          employees={employees}
          editing={editing}
          onUpdate={(qaUpdates) => {
            setFormData({ ...formData, ...qaUpdates });
          }}
        />

        <div className="detail-section">
          <h2>Progress History</h2>
          {amendment.progress_entries && amendment.progress_entries.length > 0 ? (
            <div className="progress-list">
              {amendment.progress_entries.map(entry => (
                <div key={entry.amendment_progress_id} className="progress-entry">
                  <div className="progress-header">
                    <strong>{entry.description}</strong>
                    <span className="progress-date">{formatDate(entry.created_on)}</span>
                  </div>
                  {entry.notes && <div className="progress-notes">{entry.notes}</div>}
                  {entry.created_by && <div className="progress-meta">By: {entry.created_by}</div>}
                </div>
              ))}
            </div>
          ) : (
            <p>No progress entries yet.</p>
          )}
        </div>

        <div className="detail-section">
          <h2>Applications</h2>
          {amendment.applications && amendment.applications.length > 0 ? (
            <div className="documents-list">
              <table className="documents-table">
                <thead>
                  <tr>
                    <th>Application</th>
                    <th>Reported Version</th>
                    <th>Applied Version</th>
                    <th>Dev Status</th>
                  </tr>
                </thead>
                <tbody>
                  {amendment.applications.map(app => (
                    <tr key={app.id}>
                      <td><strong>{app.application_name}</strong></td>
                      <td>{app.reported_version || 'N/A'}</td>
                      <td>{app.applied_version || 'N/A'}</td>
                      <td>{app.development_status || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>No applications linked yet.</p>
          )}
        </div>

        <div className="detail-section">
          <h2>Documents</h2>
          {amendment.documents && amendment.documents.length > 0 ? (
            <div className="documents-list">
              <table className="documents-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Size</th>
                    <th>Uploaded</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {amendment.documents.map(doc => (
                    <tr key={doc.document_id}>
                      <td>
                        <strong>{doc.document_name}</strong>
                        {doc.description && <div className="doc-description">{doc.description}</div>}
                      </td>
                      <td>{doc.document_type}</td>
                      <td>{doc.file_size ? `${(doc.file_size / 1024).toFixed(1)} KB` : 'N/A'}</td>
                      <td>
                        {formatDate(doc.uploaded_on)}
                        {doc.uploaded_by && <div className="doc-meta">By: {doc.uploaded_by}</div>}
                      </td>
                      <td>
                        <button
                          className="btn-small btn-download"
                          onClick={() => handleDownloadDocument(doc.document_id, doc.original_filename)}
                        >
                          Download
                        </button>
                        <button
                          className="btn-small btn-delete"
                          onClick={() => handleDeleteDocument(doc.document_id)}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>No documents attached yet.</p>
          )}
        </div>

        <div className="detail-section">
          <h2>Metadata</h2>
          <div className="detail-grid">
            <div className="detail-field">
              <label>Created On</label>
              <div>{formatDate(amendment.created_on)}</div>
            </div>
            <div className="detail-field">
              <label>Created By</label>
              <div>{amendment.created_by || 'N/A'}</div>
            </div>
            <div className="detail-field">
              <label>Modified On</label>
              <div>{formatDate(amendment.modified_on)}</div>
            </div>
            <div className="detail-field">
              <label>Modified By</label>
              <div>{amendment.modified_by || 'N/A'}</div>
            </div>
          </div>
        </div>
      </div>

      {showProgressModal && (
        <div className="modal-overlay" onClick={() => setShowProgressModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Add Progress Update</h2>
            <div className="modal-body">
              <div className="form-field">
                <label>Description *</label>
                <input
                  type="text"
                  value={progressData.description}
                  onChange={(e) => setProgressData({...progressData, description: e.target.value})}
                  placeholder="Brief description of progress"
                />
              </div>
              <div className="form-field">
                <label>Notes</label>
                <textarea
                  value={progressData.notes}
                  onChange={(e) => setProgressData({...progressData, notes: e.target.value})}
                  placeholder="Additional details"
                  rows="4"
                />
              </div>
              <div className="form-field">
                <label>Date</label>
                <input
                  type="datetime-local"
                  value={progressData.start_date}
                  onChange={(e) => setProgressData({...progressData, start_date: e.target.value})}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-primary" onClick={handleAddProgress}>Add Progress</button>
              <button className="btn btn-secondary" onClick={() => setShowProgressModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      {showDocumentModal && (
        <div className="modal-overlay" onClick={() => setShowDocumentModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Upload Document</h2>
            <div className="modal-body">
              <div className="form-field">
                <label>Select File *</label>
                <input
                  type="file"
                  onChange={handleFileSelect}
                  accept="*/*"
                />
                {uploadFile && <div className="file-info">Selected: {uploadFile.name}</div>}
              </div>
              <div className="form-field">
                <label>Document Name *</label>
                <input
                  type="text"
                  value={documentData.document_name}
                  onChange={(e) => setDocumentData({...documentData, document_name: e.target.value})}
                  placeholder="Enter a display name for this document"
                />
              </div>
              <div className="form-field">
                <label>Document Type</label>
                <select
                  value={documentData.document_type}
                  onChange={(e) => setDocumentData({...documentData, document_type: e.target.value})}
                >
                  <option value="Test Plan">Test Plan</option>
                  <option value="Screenshot">Screenshot</option>
                  <option value="Specification">Specification</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div className="form-field">
                <label>Description</label>
                <textarea
                  value={documentData.description}
                  onChange={(e) => setDocumentData({...documentData, description: e.target.value})}
                  placeholder="Optional description"
                  rows="3"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button
                className="btn btn-primary"
                onClick={handleUploadDocument}
                disabled={uploading || !uploadFile}
              >
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
              <button className="btn btn-secondary" onClick={() => setShowDocumentModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AmendmentDetail;
