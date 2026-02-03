import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { amendmentAPI, referenceAPI, employeeAPI, documentAPI } from '../services/api';
import QASection from '../components/QASection';

function AmendmentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [amendment, setAmendment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({});
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('general');

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

  const handleEdit = () => setEditing(true);
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
        setDocumentData(prev => ({ ...prev, document_name: file.name }));
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
      const formDataObj = new FormData();
      formDataObj.append('file', uploadFile);
      formDataObj.append('document_name', documentData.document_name);
      formDataObj.append('document_type', documentData.document_type);
      if (documentData.description) {
        formDataObj.append('description', documentData.description);
      }

      await documentAPI.upload(id, formDataObj);
      setShowDocumentModal(false);
      setUploadFile(null);
      setDocumentData({ document_name: '', document_type: 'Other', description: '' });
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
    return new Date(dateString).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const getPriorityClass = (priority) => {
    if (priority === 'Critical') return 'text-red-600';
    if (priority === 'High') return 'text-orange-600';
    return 'text-gray-600';
  };

  if (loading) {
    return (
      <div className="max-w-[1440px] mx-auto px-6 py-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading amendment...</div>
        </div>
      </div>
    );
  }

  if (error && !amendment) {
    return (
      <div className="max-w-[1440px] mx-auto px-6 py-6">
        <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-4">{error}</div>
        <button
          onClick={() => navigate('/amendments')}
          className="px-4 py-2 bg-gray-100 rounded-lg text-sm font-medium hover:bg-gray-200"
        >
          Back to List
        </button>
      </div>
    );
  }

  const tabs = [
    { id: 'general', label: 'General Info', icon: 'info' },
    { id: 'qa', label: 'QA Testing', icon: 'fact_check' },
    { id: 'history', label: 'History', icon: 'history' },
    { id: 'attachments', label: 'Attachments', icon: 'attach_file' },
  ];

  return (
    <div className="max-w-[1440px] mx-auto px-6 py-6">
      {/* Breadcrumbs */}
      <div className="flex flex-wrap gap-2 mb-2">
        <Link to="/dashboard" className="text-gray-500 text-sm font-medium hover:underline">System</Link>
        <span className="text-gray-500 text-sm font-medium">/</span>
        <Link to="/amendments" className="text-gray-500 text-sm font-medium hover:underline">Amendments</Link>
        <span className="text-gray-500 text-sm font-medium">/</span>
        <span className="text-gray-900 dark:text-white text-sm font-bold">{amendment.amendment_reference}</span>
      </div>

      {/* Page Heading */}
      <div className="flex flex-wrap justify-between items-start gap-4 mb-8">
        <div className="flex flex-col gap-1">
          <h1 className="text-gray-900 dark:text-white text-3xl font-black leading-tight tracking-tight">
            {amendment.amendment_reference}: {amendment.description?.substring(0, 50)}{amendment.description?.length > 50 ? '...' : ''}
          </h1>
          <p className="text-gray-500 text-sm">
            Created on {formatDate(amendment.created_on)} by {amendment.created_by || 'Unknown'}
            {amendment.modified_on && ` • Last updated ${formatDate(amendment.modified_on)}`}
          </p>
        </div>
        <div className="flex gap-3">
          {!editing ? (
            <>
              <button
                onClick={handleEdit}
                className="flex items-center justify-center rounded-lg h-10 px-4 bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white text-sm font-bold hover:bg-gray-200 dark:hover:bg-white/20 transition-colors"
              >
                <span className="material-symbols-outlined mr-2 text-lg">edit</span> Edit
              </button>
              <button
                onClick={() => setShowProgressModal(true)}
                className="flex items-center justify-center rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold hover:bg-primary/90 shadow-md"
              >
                <span className="material-symbols-outlined mr-2 text-lg">add</span> Add Progress
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleCancel}
                className="flex items-center justify-center rounded-lg h-10 px-4 bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white text-sm font-bold hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center justify-center rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold hover:bg-primary/90 shadow-md disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </>
          )}
        </div>
      </div>

      {error && <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-4">{error}</div>}

      {/* Two-Column Layout */}
      <div className="grid grid-cols-12 gap-6">
        {/* Left Column (Tabs & Main Content) */}
        <div className="col-span-12 lg:col-span-8 space-y-6">
          <div className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl overflow-hidden shadow-sm">
            {/* Tabs */}
            <div className="flex border-b border-gray-200 dark:border-white/10 px-6 gap-8 bg-gray-50 dark:bg-white/5">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center border-b-2 py-4 font-bold text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-primary text-primary'
                      : 'border-transparent text-gray-500 hover:text-primary'
                  }`}
                >
                  <span className="material-symbols-outlined mr-2 text-lg">{tab.icon}</span> {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="p-6">
              {activeTab === 'general' && (
                <div className="space-y-6">
                  {/* Details Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Type</label>
                      {editing ? (
                        <select
                          name="amendment_type"
                          value={formData.amendment_type}
                          onChange={handleChange}
                          className="w-full rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                        >
                          {types.map(type => <option key={type} value={type}>{type}</option>)}
                        </select>
                      ) : (
                        <p className="text-sm font-medium">{amendment.amendment_type}</p>
                      )}
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Force</label>
                      {editing ? (
                        <select
                          name="force"
                          value={formData.force || ''}
                          onChange={handleChange}
                          className="w-full rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                        >
                          <option value="">None</option>
                          {forces.map(force => <option key={force} value={force}>{force}</option>)}
                        </select>
                      ) : (
                        <p className="text-sm font-medium">{amendment.force || 'N/A'}</p>
                      )}
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Application</label>
                      {editing ? (
                        <input
                          type="text"
                          name="application"
                          value={formData.application || ''}
                          onChange={handleChange}
                          className="w-full rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                        />
                      ) : (
                        <p className="text-sm font-medium">{amendment.application || 'N/A'}</p>
                      )}
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Date Reported</label>
                      {editing ? (
                        <input
                          type="datetime-local"
                          name="date_reported"
                          value={formData.date_reported ? new Date(formData.date_reported).toISOString().slice(0, 16) : ''}
                          onChange={handleChange}
                          className="w-full rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                        />
                      ) : (
                        <p className="text-sm font-medium">{formatDateTime(amendment.date_reported)}</p>
                      )}
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Reported By</label>
                      {editing ? (
                        <select
                          name="reported_by"
                          value={formData.reported_by || ''}
                          onChange={handleChange}
                          className="w-full rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                        >
                          <option value="">Select Reporter</option>
                          {employees.map(emp => (
                            <option key={emp.employee_id} value={emp.initials}>{emp.employee_name} ({emp.initials})</option>
                          ))}
                        </select>
                      ) : (
                        <p className="text-sm font-medium">{amendment.reported_by || 'N/A'}</p>
                      )}
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Assigned To</label>
                      {editing ? (
                        <select
                          name="assigned_to"
                          value={formData.assigned_to || ''}
                          onChange={handleChange}
                          className="w-full rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                        >
                          <option value="">Select Assignee</option>
                          {employees.map(emp => (
                            <option key={emp.employee_id} value={emp.initials}>{emp.employee_name} ({emp.initials})</option>
                          ))}
                        </select>
                      ) : (
                        <p className="text-sm font-medium">{amendment.assigned_to || 'N/A'}</p>
                      )}
                    </div>
                  </div>

                  {/* Description */}
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Description</label>
                    {editing ? (
                      <textarea
                        name="description"
                        value={formData.description}
                        onChange={handleChange}
                        rows="4"
                        className="w-full rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                      />
                    ) : (
                      <p className="text-sm leading-relaxed bg-gray-50 dark:bg-white/5 p-4 rounded-lg">{amendment.description}</p>
                    )}
                  </div>

                  {/* Notes */}
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Notes</label>
                    {editing ? (
                      <textarea
                        name="notes"
                        value={formData.notes || ''}
                        onChange={handleChange}
                        rows="4"
                        className="w-full rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                      />
                    ) : (
                      <p className="text-sm leading-relaxed bg-gray-50 dark:bg-white/5 p-4 rounded-lg">{amendment.notes || 'No notes'}</p>
                    )}
                  </div>

                  {/* Release Notes */}
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Release Notes</label>
                    {editing ? (
                      <textarea
                        name="release_notes"
                        value={formData.release_notes || ''}
                        onChange={handleChange}
                        rows="4"
                        className="w-full rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                      />
                    ) : (
                      <p className="text-sm leading-relaxed bg-gray-50 dark:bg-white/5 p-4 rounded-lg">{amendment.release_notes || 'No release notes'}</p>
                    )}
                  </div>

                  {/* Checkboxes */}
                  <div className="flex flex-wrap gap-6">
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        name="database_changes"
                        checked={editing ? formData.database_changes : amendment.database_changes}
                        onChange={handleChange}
                        disabled={!editing}
                        className="rounded border-gray-300 text-primary focus:ring-primary"
                      />
                      Database Changes
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        name="db_upgrade_changes"
                        checked={editing ? formData.db_upgrade_changes : amendment.db_upgrade_changes}
                        onChange={handleChange}
                        disabled={!editing}
                        className="rounded border-gray-300 text-primary focus:ring-primary"
                      />
                      DB Upgrade Changes
                    </label>
                  </div>

                  {/* Applications */}
                  {amendment.applications && amendment.applications.length > 0 && (
                    <div className="space-y-3">
                      <h3 className="text-sm font-bold">Linked Applications</h3>
                      <div className="border border-gray-200 dark:border-white/10 rounded-lg overflow-hidden">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-50 dark:bg-white/5">
                            <tr>
                              <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase">Application</th>
                              <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase">Reported Ver.</th>
                              <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase">Applied Ver.</th>
                              <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase">Status</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-200 dark:divide-white/10">
                            {amendment.applications.map(app => (
                              <tr key={app.id}>
                                <td className="px-4 py-3 font-medium">{app.application_name}</td>
                                <td className="px-4 py-3 text-gray-500">{app.reported_version || 'N/A'}</td>
                                <td className="px-4 py-3 text-gray-500">{app.applied_version || 'N/A'}</td>
                                <td className="px-4 py-3 text-gray-500">{app.development_status || 'N/A'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'qa' && (
                <QASection
                  amendment={amendment}
                  employees={employees}
                  editing={editing}
                  onUpdate={(qaUpdates) => setFormData({ ...formData, ...qaUpdates })}
                />
              )}

              {activeTab === 'history' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold">Progress History</h3>
                    <button
                      onClick={() => setShowProgressModal(true)}
                      className="flex items-center gap-2 text-sm font-bold text-primary hover:underline"
                    >
                      <span className="material-symbols-outlined text-lg">add</span> Add Entry
                    </button>
                  </div>
                  {amendment.progress_entries && amendment.progress_entries.length > 0 ? (
                    <div className="space-y-3">
                      {amendment.progress_entries.map(entry => (
                        <div key={entry.amendment_progress_id} className="border border-gray-200 dark:border-white/10 rounded-lg p-4 bg-gray-50/50 dark:bg-white/5">
                          <div className="flex items-start justify-between mb-2">
                            <h4 className="font-bold text-sm">{entry.description}</h4>
                            <span className="text-xs text-gray-500">{formatDateTime(entry.created_on)}</span>
                          </div>
                          {entry.notes && <p className="text-sm text-gray-600 dark:text-gray-400">{entry.notes}</p>}
                          {entry.created_by && <p className="text-xs text-gray-500 mt-2">By: {entry.created_by}</p>}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-sm">No progress entries yet.</p>
                  )}
                </div>
              )}

              {activeTab === 'attachments' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold">Documents</h3>
                    <button
                      onClick={() => setShowDocumentModal(true)}
                      className="flex items-center gap-2 text-sm font-bold text-primary hover:underline"
                    >
                      <span className="material-symbols-outlined text-lg">upload</span> Upload Document
                    </button>
                  </div>
                  {amendment.documents && amendment.documents.length > 0 ? (
                    <div className="space-y-3">
                      {amendment.documents.map(doc => (
                        <div key={doc.document_id} className="flex items-center justify-between border border-gray-200 dark:border-white/10 rounded-lg p-4">
                          <div className="flex items-center gap-4">
                            <div className="w-10 h-10 bg-gray-100 dark:bg-white/10 rounded-lg flex items-center justify-center">
                              <span className="material-symbols-outlined text-gray-500">description</span>
                            </div>
                            <div>
                              <h4 className="font-bold text-sm">{doc.document_name}</h4>
                              <p className="text-xs text-gray-500">
                                {doc.document_type} • {doc.file_size ? `${(doc.file_size / 1024).toFixed(1)} KB` : 'Unknown size'} • {formatDate(doc.uploaded_on)}
                              </p>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleDownloadDocument(doc.document_id, doc.original_filename)}
                              className="p-2 text-primary hover:bg-primary/10 rounded-lg transition-colors"
                            >
                              <span className="material-symbols-outlined">download</span>
                            </button>
                            <button
                              onClick={() => handleDeleteDocument(doc.document_id)}
                              className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                            >
                              <span className="material-symbols-outlined">delete</span>
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <span className="material-symbols-outlined text-4xl text-gray-300 mb-2">folder_open</span>
                      <p className="text-gray-500 text-sm">No documents attached yet</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Sidebar (Metadata Panel) */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-6">
          {/* Status & SLA Card */}
          <div className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl p-5 shadow-sm">
            <h3 className="text-xs font-black uppercase tracking-widest text-gray-500 mb-4">Lifecycle Status</h3>
            <div className="flex items-center gap-3 mb-6">
              {editing ? (
                <select
                  name="amendment_status"
                  value={formData.amendment_status}
                  onChange={handleChange}
                  className="flex-1 rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm font-bold"
                >
                  {statuses.map(status => <option key={status} value={status}>{status}</option>)}
                </select>
              ) : (
                <span className="flex-1 px-4 py-2 bg-primary/10 text-primary text-sm font-bold rounded-lg border border-primary/20 text-center">
                  {amendment.amendment_status}
                </span>
              )}
            </div>
            <div className="space-y-4">
              <div className="flex justify-between items-center pb-3 border-b border-gray-100 dark:border-white/10">
                <span className="text-sm text-gray-500">Priority</span>
                {editing ? (
                  <select
                    name="priority"
                    value={formData.priority}
                    onChange={handleChange}
                    className="rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm font-bold"
                  >
                    {priorities.map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                ) : (
                  <span className={`flex items-center gap-1.5 text-sm font-bold ${getPriorityClass(amendment.priority)}`}>
                    {amendment.priority === 'Critical' && <span className="w-2 h-2 rounded-full bg-red-600"></span>}
                    {amendment.priority === 'High' && <span className="w-2 h-2 rounded-full bg-orange-500"></span>}
                    {amendment.priority}
                  </span>
                )}
              </div>
              <div className="flex justify-between items-center pb-3 border-b border-gray-100 dark:border-white/10">
                <span className="text-sm text-gray-500">Dev Status</span>
                {editing ? (
                  <select
                    name="development_status"
                    value={formData.development_status}
                    onChange={handleChange}
                    className="rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm font-bold"
                  >
                    {devStatuses.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                ) : (
                  <span className="text-sm font-bold text-gray-900 dark:text-white">{amendment.development_status}</span>
                )}
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">QA Status</span>
                <span className={`text-sm font-bold ${amendment.qa_completed ? 'text-green-600' : 'text-gray-600'}`}>
                  {amendment.qa_completed ? 'Completed' : 'Pending'}
                </span>
              </div>
            </div>
          </div>

          {/* Personnel Card */}
          <div className="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl p-5 shadow-sm">
            <h3 className="text-xs font-black uppercase tracking-widest text-gray-500 mb-4">Personnel</h3>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold text-sm">
                  {amendment.assigned_to ? amendment.assigned_to.substring(0, 2).toUpperCase() : '?'}
                </div>
                <div>
                  <p className="text-sm font-bold">{amendment.assigned_to || 'Unassigned'}</p>
                  <p className="text-xs text-gray-500">Assigned Developer</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-white/10 flex items-center justify-center text-gray-600 font-bold text-sm">
                  {amendment.reported_by ? amendment.reported_by.substring(0, 2).toUpperCase() : '?'}
                </div>
                <div>
                  <p className="text-sm font-bold">{amendment.reported_by || 'Unknown'}</p>
                  <p className="text-xs text-gray-500">Reporter</p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Metadata Grid */}
          <div className="bg-gray-900 text-white rounded-xl p-5 shadow-lg">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <p className="text-[10px] text-gray-400 uppercase font-bold tracking-widest">Reference</p>
                <p className="text-xs font-bold font-mono">{amendment.amendment_reference}</p>
              </div>
              <div className="space-y-1 text-right">
                <p className="text-[10px] text-gray-400 uppercase font-bold tracking-widest">Application</p>
                <p className="text-xs font-bold">{amendment.application || 'N/A'}</p>
              </div>
              <div className="space-y-1">
                <p className="text-[10px] text-gray-400 uppercase font-bold tracking-widest">Type</p>
                <p className="text-xs font-bold">{amendment.amendment_type}</p>
              </div>
              <div className="space-y-1 text-right">
                <p className="text-[10px] text-gray-400 uppercase font-bold tracking-widest">Force</p>
                <p className="text-xs font-bold">{amendment.force || 'N/A'}</p>
              </div>
            </div>
          </div>

          {/* Danger Zone */}
          <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 rounded-xl p-5">
            <h3 className="text-xs font-black uppercase tracking-widest text-red-600 mb-3">Danger Zone</h3>
            <button
              onClick={handleDelete}
              className="w-full py-2 px-4 border border-red-300 dark:border-red-800 text-red-600 text-sm font-bold rounded-lg hover:bg-red-100 dark:hover:bg-red-900/20 transition-colors"
            >
              Delete Amendment
            </button>
          </div>
        </div>
      </div>

      {/* Progress Modal */}
      {showProgressModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowProgressModal(false)}>
          <div className="bg-white dark:bg-background-dark rounded-xl p-6 max-w-md w-full mx-4 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-4">Add Progress Update</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Description *</label>
                <input
                  type="text"
                  value={progressData.description}
                  onChange={(e) => setProgressData({...progressData, description: e.target.value})}
                  placeholder="Brief description of progress"
                  className="w-full rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Notes</label>
                <textarea
                  value={progressData.notes}
                  onChange={(e) => setProgressData({...progressData, notes: e.target.value})}
                  placeholder="Additional details"
                  rows="4"
                  className="w-full rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Date</label>
                <input
                  type="datetime-local"
                  value={progressData.start_date}
                  onChange={(e) => setProgressData({...progressData, start_date: e.target.value})}
                  className="w-full rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowProgressModal(false)}
                className="flex-1 py-2 bg-gray-100 dark:bg-white/10 rounded-lg font-bold text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleAddProgress}
                className="flex-1 py-2 bg-primary text-white rounded-lg font-bold text-sm"
              >
                Add Progress
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Document Upload Modal */}
      {showDocumentModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowDocumentModal(false)}>
          <div className="bg-white dark:bg-background-dark rounded-xl p-6 max-w-md w-full mx-4 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-4">Upload Document</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Select File *</label>
                <input
                  type="file"
                  onChange={handleFileSelect}
                  accept="*/*"
                  className="w-full text-sm"
                />
                {uploadFile && <p className="text-xs text-gray-500 mt-1">Selected: {uploadFile.name}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Document Name *</label>
                <input
                  type="text"
                  value={documentData.document_name}
                  onChange={(e) => setDocumentData({...documentData, document_name: e.target.value})}
                  placeholder="Enter a display name"
                  className="w-full rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Document Type</label>
                <select
                  value={documentData.document_type}
                  onChange={(e) => setDocumentData({...documentData, document_type: e.target.value})}
                  className="w-full rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                >
                  <option value="Test Plan">Test Plan</option>
                  <option value="Screenshot">Screenshot</option>
                  <option value="Specification">Specification</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={documentData.description}
                  onChange={(e) => setDocumentData({...documentData, description: e.target.value})}
                  placeholder="Optional description"
                  rows="3"
                  className="w-full rounded-lg border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-sm"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowDocumentModal(false)}
                className="flex-1 py-2 bg-gray-100 dark:bg-white/10 rounded-lg font-bold text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleUploadDocument}
                disabled={uploading || !uploadFile}
                className="flex-1 py-2 bg-primary text-white rounded-lg font-bold text-sm disabled:opacity-50"
              >
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AmendmentDetail;
