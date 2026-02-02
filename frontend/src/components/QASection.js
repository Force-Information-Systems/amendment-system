import React, { useState, useEffect } from 'react';
import { amendmentAPI } from '../services/api';
import { StatusBadge, ProgressBar, QAComments, WatcherButton } from './qa';
import './QASection.css';

// Get API base URL from environment or default to /api (for proxy)
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

function QASection({ amendment, employees, onUpdate, editing }) {
  const [qaData, setQaData] = useState({
    qa_status: amendment.qa_status || 'Not Started',
    qa_assigned_id: amendment.qa_assigned_id || null,
    qa_assigned_date: amendment.qa_assigned_date || null,
    qa_started_date: amendment.qa_started_date || null,
    qa_test_plan_check: amendment.qa_test_plan_check || false,
    qa_test_release_notes_check: amendment.qa_test_release_notes_check || false,
    qa_completed: amendment.qa_completed || false,
    qa_signature: amendment.qa_signature || '',
    qa_completed_date: amendment.qa_completed_date || null,
    qa_notes: amendment.qa_notes || '',
    qa_test_plan_link: amendment.qa_test_plan_link || '',
    qa_blocked_reason: amendment.qa_blocked_reason || '',
    qa_overall_result: amendment.qa_overall_result || null,
  });

  const [qaProgress, setQaProgress] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showNotesModal, setShowNotesModal] = useState(false);

  useEffect(() => {
    setQaData({
      qa_status: amendment.qa_status || 'Not Started',
      qa_assigned_id: amendment.qa_assigned_id || null,
      qa_assigned_date: amendment.qa_assigned_date || null,
      qa_started_date: amendment.qa_started_date || null,
      qa_test_plan_check: amendment.qa_test_plan_check || false,
      qa_test_release_notes_check: amendment.qa_test_release_notes_check || false,
      qa_completed: amendment.qa_completed || false,
      qa_signature: amendment.qa_signature || '',
      qa_completed_date: amendment.qa_completed_date || null,
      qa_notes: amendment.qa_notes || '',
      qa_test_plan_link: amendment.qa_test_plan_link || '',
      qa_blocked_reason: amendment.qa_blocked_reason || '',
      qa_overall_result: amendment.qa_overall_result || null,
    });

    // Load QA progress
    loadQAProgress();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [amendment]);

  const loadQAProgress = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/amendments/${amendment.amendment_id}/qa-progress`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      if (response.ok) {
        const progress = await response.json();
        setQaProgress(progress);
      }
    } catch (error) {
      console.error('Failed to load QA progress:', error);
    }
  };

  const getAssignedEmployee = () => {
    if (!qaData.qa_assigned_id) return null;
    return employees.find(e => e.employee_id === qaData.qa_assigned_id);
  };

  const handleStatusChange = async (newStatus) => {
    const updates = { ...qaData, qa_status: newStatus };

    if (newStatus === 'In Testing' && !qaData.qa_started_date) {
      updates.qa_started_date = new Date().toISOString();
    }

    if (newStatus === 'Passed' || newStatus === 'Failed') {
      updates.qa_completed = true;
      updates.qa_completed_date = new Date().toISOString();
    }

    setQaData(updates);

    try {
      await amendmentAPI.updateQA(amendment.amendment_id, updates);
      if (onUpdate) {
        onUpdate(updates);
      }
    } catch (error) {
      console.error('Failed to update QA status:', error);
      // Revert on error
      setQaData(qaData);
    }
  };

  const handleAssign = async (employeeId) => {
    const updates = {
      ...qaData,
      qa_assigned_id: employeeId,
      qa_assigned_date: new Date().toISOString(),
      qa_status: qaData.qa_status === 'Not Started' ? 'Assigned' : qaData.qa_status,
    };
    setQaData(updates);
    setShowAssignModal(false);

    try {
      await amendmentAPI.updateQA(amendment.amendment_id, updates);
      if (onUpdate) {
        onUpdate(updates);
      }
    } catch (error) {
      console.error('Failed to assign QA:', error);
      setQaData(qaData);
    }
  };

  const handleChecklistChange = async (field) => {
    const updates = { ...qaData, [field]: !qaData[field] };
    setQaData(updates);

    try {
      await amendmentAPI.updateQA(amendment.amendment_id, updates);
      if (onUpdate) {
        onUpdate(updates);
      }
    } catch (error) {
      console.error('Failed to update checklist:', error);
      setQaData(qaData);
    }
  };

  const handleSaveNotes = async () => {
    setShowNotesModal(false);

    try {
      await amendmentAPI.updateQA(amendment.amendment_id, qaData);
      if (onUpdate) {
        onUpdate(qaData);
      }
    } catch (error) {
      console.error('Failed to save notes:', error);
    }
  };

  const handleFieldBlur = async () => {
    try {
      await amendmentAPI.updateQA(amendment.amendment_id, qaData);
      if (onUpdate) {
        onUpdate(qaData);
      }
    } catch (error) {
      console.error('Failed to update field:', error);
    }
  };

  const handleOverallResultChange = async (result) => {
    const updates = { ...qaData, qa_overall_result: result };
    setQaData(updates);

    try {
      await amendmentAPI.updateQA(amendment.amendment_id, updates);
      if (onUpdate) {
        onUpdate(updates);
      }
    } catch (error) {
      console.error('Failed to update overall result:', error);
      setQaData(qaData);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Not set';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const assignedEmployee = getAssignedEmployee();
  const completionPercentage = qaData.qa_test_plan_check && qaData.qa_test_release_notes_check ? 100 :
                                 qaData.qa_test_plan_check || qaData.qa_test_release_notes_check ? 50 : 0;

  const getCurrentUser = () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  };

  return (
    <div className="qa-section">
      <div className="qa-header">
        <div className="qa-header-left">
          <h3>Quality Assurance</h3>
          <StatusBadge status={qaData.qa_status} showIcon={true} size="large" />
        </div>
        <WatcherButton amendmentId={amendment.amendment_id} />
      </div>

      {/* Overall Result & Progress Summary */}
      <div className="qa-summary-card">
        <div className="qa-summary-row">
          <div className="qa-summary-item">
            <label>Overall Result:</label>
            {editing ? (
              <select
                className="qa-overall-result-select"
                value={qaData.qa_overall_result || ''}
                onChange={(e) => handleOverallResultChange(e.target.value || null)}
              >
                <option value="">Not Set</option>
                <option value="Passed">✅ Passed</option>
                <option value="Failed">❌ Failed</option>
                <option value="Passed with Issues">⚠️ Passed with Issues</option>
              </select>
            ) : (
              <div>
                {qaData.qa_overall_result ? (
                  <StatusBadge status={qaData.qa_overall_result} showIcon={true} size="medium" />
                ) : (
                  <span className="qa-empty-inline">Not Set</span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Progress Summary */}
        {qaProgress && (
          <div className="qa-progress-summary">
            <div className="qa-progress-row">
              <ProgressBar
                completed={qaProgress.tests_passed}
                total={qaProgress.total_tests}
                label="Test Execution"
                showPercentage={true}
                showFraction={true}
                color="auto"
                size="medium"
              />
            </div>
            <div className="qa-progress-row">
              <ProgressBar
                completed={qaProgress.checklist_items_completed}
                total={qaProgress.checklist_items_total}
                label="Checklist"
                showPercentage={true}
                showFraction={true}
                color="auto"
                size="medium"
              />
            </div>
            {qaProgress.total_tests > 0 && (
              <div className="qa-test-summary">
                <span className="qa-test-stat">✅ {qaProgress.tests_passed} Passed</span>
                <span className="qa-test-stat">❌ {qaProgress.tests_failed} Failed</span>
                <span className="qa-test-stat">⚠️ {qaProgress.tests_blocked} Blocked</span>
                <span className="qa-test-stat">⏸️ {qaProgress.tests_not_run} Not Run</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="qa-tabs">
        <button
          className={`qa-tab ${activeTab === 'overview' ? 'qa-tab-active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`qa-tab ${activeTab === 'comments' ? 'qa-tab-active' : ''}`}
          onClick={() => setActiveTab('comments')}
        >
          Comments {qaProgress && qaProgress.total_comments > 0 && `(${qaProgress.total_comments})`}
        </button>
      </div>

      <div className="qa-content">
        {activeTab === 'overview' && (
          <>
        {/* Assignee Section */}
        <div className="qa-card">
          <div className="qa-card-header">
            <h4>Assignee</h4>
            {editing && (
              <button className="qa-btn qa-btn-sm" onClick={() => setShowAssignModal(true)}>
                {assignedEmployee ? 'Change' : 'Assign'}
              </button>
            )}
          </div>
          <div className="qa-card-body">
            {assignedEmployee ? (
              <div className="qa-assignee">
                <div className="qa-avatar">
                  {assignedEmployee.initials || assignedEmployee.employee_name.split(' ').map(n => n[0]).join('')}
                </div>
                <div className="qa-assignee-info">
                  <div className="qa-assignee-name">{assignedEmployee.employee_name}</div>
                  <div className="qa-assignee-date">Assigned {formatDate(qaData.qa_assigned_date)}</div>
                </div>
              </div>
            ) : (
              <div className="qa-empty">No one assigned</div>
            )}
          </div>
        </div>

        {/* Status Workflow */}
        {editing && (
          <div className="qa-card">
            <div className="qa-card-header">
              <h4>Update Status</h4>
            </div>
            <div className="qa-card-body">
              <div className="qa-status-buttons">
                <button
                  className={`qa-status-btn ${qaData.qa_status === 'Assigned' ? 'active' : ''}`}
                  onClick={() => handleStatusChange('Assigned')}
                  disabled={!qaData.qa_assigned_id}
                >
                  🎯 Assigned
                </button>
                <button
                  className={`qa-status-btn ${qaData.qa_status === 'In Testing' ? 'active' : ''}`}
                  onClick={() => handleStatusChange('In Testing')}
                  disabled={!qaData.qa_assigned_id}
                >
                  🔬 In Testing
                </button>
                <button
                  className={`qa-status-btn ${qaData.qa_status === 'Blocked' ? 'active' : ''}`}
                  onClick={() => handleStatusChange('Blocked')}
                >
                  🚫 Blocked
                </button>
                <button
                  className={`qa-status-btn ${qaData.qa_status === 'Passed' ? 'active' : ''}`}
                  onClick={() => handleStatusChange('Passed')}
                  style={{ background: qaData.qa_status === 'Passed' ? '#28a745' : '' }}
                >
                  ✅ Passed
                </button>
                <button
                  className={`qa-status-btn ${qaData.qa_status === 'Failed' ? 'active' : ''}`}
                  onClick={() => handleStatusChange('Failed')}
                  style={{ background: qaData.qa_status === 'Failed' ? '#dc3545' : '' }}
                >
                  ❌ Failed
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Test Checklist */}
        <div className="qa-card">
          <div className="qa-card-header">
            <h4>Test Checklist</h4>
            <span className="qa-progress-text">{completionPercentage}% Complete</span>
          </div>
          <div className="qa-card-body">
            <div className="qa-progress-bar">
              <div
                className="qa-progress-fill"
                style={{ width: `${completionPercentage}%` }}
              ></div>
            </div>
            <div className="qa-checklist">
              <label className="qa-checkbox">
                <input
                  type="checkbox"
                  checked={qaData.qa_test_plan_check}
                  onChange={() => editing && handleChecklistChange('qa_test_plan_check')}
                  disabled={!editing}
                />
                <span className={qaData.qa_test_plan_check ? 'checked' : ''}>
                  Test plan verified and executed
                </span>
              </label>
              <label className="qa-checkbox">
                <input
                  type="checkbox"
                  checked={qaData.qa_test_release_notes_check}
                  onChange={() => editing && handleChecklistChange('qa_test_release_notes_check')}
                  disabled={!editing}
                />
                <span className={qaData.qa_test_release_notes_check ? 'checked' : ''}>
                  Release notes reviewed and accurate
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Test Plan Link */}
        {(qaData.qa_test_plan_link || editing) && (
          <div className="qa-card">
            <div className="qa-card-header">
              <h4>Test Plan</h4>
            </div>
            <div className="qa-card-body">
              {editing ? (
                <input
                  type="text"
                  className="qa-input"
                  value={qaData.qa_test_plan_link}
                  onChange={(e) => setQaData({ ...qaData, qa_test_plan_link: e.target.value })}
                  onBlur={handleFieldBlur}
                  placeholder="Enter test plan URL or path"
                />
              ) : qaData.qa_test_plan_link ? (
                <a href={qaData.qa_test_plan_link} target="_blank" rel="noopener noreferrer" className="qa-link">
                  {qaData.qa_test_plan_link}
                </a>
              ) : (
                <div className="qa-empty">No test plan link provided</div>
              )}
            </div>
          </div>
        )}

        {/* Timeline */}
        <div className="qa-card">
          <div className="qa-card-header">
            <h4>Timeline</h4>
          </div>
          <div className="qa-card-body">
            <div className="qa-timeline">
              {qaData.qa_assigned_date && (
                <div className="qa-timeline-item">
                  <div className="qa-timeline-dot"></div>
                  <div className="qa-timeline-content">
                    <div className="qa-timeline-title">Assigned to QA</div>
                    <div className="qa-timeline-date">{formatDate(qaData.qa_assigned_date)}</div>
                  </div>
                </div>
              )}
              {qaData.qa_started_date && (
                <div className="qa-timeline-item">
                  <div className="qa-timeline-dot"></div>
                  <div className="qa-timeline-content">
                    <div className="qa-timeline-title">Testing Started</div>
                    <div className="qa-timeline-date">{formatDate(qaData.qa_started_date)}</div>
                  </div>
                </div>
              )}
              {qaData.qa_completed_date && (
                <div className="qa-timeline-item">
                  <div className="qa-timeline-dot" style={{ background: qaData.qa_status === 'Passed' ? '#28a745' : '#dc3545' }}></div>
                  <div className="qa-timeline-content">
                    <div className="qa-timeline-title">QA {qaData.qa_status}</div>
                    <div className="qa-timeline-date">{formatDate(qaData.qa_completed_date)}</div>
                    {qaData.qa_signature && (
                      <div className="qa-timeline-meta">Signed off by: {qaData.qa_signature}</div>
                    )}
                  </div>
                </div>
              )}
              {!qaData.qa_assigned_date && !qaData.qa_started_date && !qaData.qa_completed_date && (
                <div className="qa-empty">No QA activity yet</div>
              )}
            </div>
          </div>
        </div>

        {/* QA Notes */}
        <div className="qa-card">
          <div className="qa-card-header">
            <h4>QA Notes</h4>
            {editing && (
              <button className="qa-btn qa-btn-sm" onClick={() => setShowNotesModal(true)}>
                {qaData.qa_notes ? 'Edit' : 'Add'} Notes
              </button>
            )}
          </div>
          <div className="qa-card-body">
            {qaData.qa_notes ? (
              <div className="qa-notes-content">{qaData.qa_notes}</div>
            ) : (
              <div className="qa-empty">No QA notes added</div>
            )}
          </div>
        </div>

        {/* Blocked Reason */}
        {qaData.qa_status === 'Blocked' && (
          <div className="qa-card qa-card-blocked">
            <div className="qa-card-header">
              <h4>🚫 Blocked - Reason</h4>
            </div>
            <div className="qa-card-body">
              {editing ? (
                <textarea
                  className="qa-textarea"
                  value={qaData.qa_blocked_reason || ''}
                  onChange={(e) => setQaData({ ...qaData, qa_blocked_reason: e.target.value })}
                  onBlur={handleFieldBlur}
                  placeholder="Why is this amendment blocked from QA?"
                  rows="3"
                />
              ) : (
                <div className="qa-notes-content">{qaData.qa_blocked_reason || 'No reason provided'}</div>
              )}
            </div>
          </div>
        )}
        </>
        )}

        {/* Comments Tab */}
        {activeTab === 'comments' && (
          <QAComments amendmentId={amendment.amendment_id} currentUser={getCurrentUser()} />
        )}
      </div>

      {/* Assign Modal */}
      {showAssignModal && (
        <div className="qa-modal" onClick={() => setShowAssignModal(false)}>
          <div className="qa-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="qa-modal-header">
              <h3>Assign to QA</h3>
              <button className="qa-modal-close" onClick={() => setShowAssignModal(false)}>×</button>
            </div>
            <div className="qa-modal-body">
              <div className="qa-employee-list">
                {employees.filter(e => e.is_active).map((employee) => (
                  <div
                    key={employee.employee_id}
                    className={`qa-employee-item ${qaData.qa_assigned_id === employee.employee_id ? 'selected' : ''}`}
                    onClick={() => handleAssign(employee.employee_id)}
                  >
                    <div className="qa-avatar">
                      {employee.initials || employee.employee_name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div className="qa-employee-name">{employee.employee_name}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Notes Modal */}
      {showNotesModal && (
        <div className="qa-modal" onClick={() => setShowNotesModal(false)}>
          <div className="qa-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="qa-modal-header">
              <h3>QA Notes</h3>
              <button className="qa-modal-close" onClick={() => setShowNotesModal(false)}>×</button>
            </div>
            <div className="qa-modal-body">
              <textarea
                className="qa-textarea"
                value={qaData.qa_notes}
                onChange={(e) => setQaData({ ...qaData, qa_notes: e.target.value })}
                placeholder="Add detailed QA notes, test results, issues found, etc."
                rows="10"
                autoFocus
              />
            </div>
            <div className="qa-modal-footer">
              <button className="qa-btn qa-btn-secondary" onClick={() => setShowNotesModal(false)}>
                Cancel
              </button>
              <button className="qa-btn qa-btn-primary" onClick={handleSaveNotes}>
                Save Notes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default QASection;
