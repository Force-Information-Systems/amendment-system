import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const QADashboard = () => {
  const navigate = useNavigate();
  const [amendments, setAmendments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [applications, setApplications] = useState([]);

  // Filters
  const [filters, setFilters] = useState({
    application: 'all',
    force: 'all',
    priority: 'all',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('No authentication token found. Please login.');
        setLoading(false);
        return;
      }

      const [amendmentsRes, appsRes, employeesRes] = await Promise.all([
        fetch(`${API_BASE_URL}/amendments?limit=1000`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_BASE_URL}/applications`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_BASE_URL}/employees`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);

      if (!amendmentsRes.ok) throw new Error('Failed to load amendments');

      const amendmentsData = await amendmentsRes.json();
      setAmendments(amendmentsData.items || []);

      if (appsRes.ok) setApplications(await appsRes.json() || []);
      if (employeesRes.ok) setEmployees(await employeesRes.json() || []);

      setLoading(false);
    } catch (err) {
      setError(`Failed to load data: ${err.message}`);
      setLoading(false);
    }
  };

  const getEmployeeName = (employeeId) => {
    if (!employeeId) return 'Unassigned';
    const emp = employees.find(e => e.employee_id === employeeId);
    return emp ? emp.employee_name : 'Unknown';
  };

  const getEmployeeInitials = (employeeId) => {
    const name = getEmployeeName(employeeId);
    if (name === 'Unassigned') return '?';
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  };

  // Filter amendments
  const filteredAmendments = amendments.filter(a => {
    if (filters.application !== 'all' && a.application !== filters.application) return false;
    if (filters.force !== 'all' && a.force !== filters.force) return false;
    if (filters.priority !== 'all' && a.priority !== filters.priority) return false;
    return true;
  });

  // Group amendments by QA status for Kanban columns
  const columns = {
    notStarted: filteredAmendments.filter(a => !a.qa_status || a.qa_status === 'Not Started'),
    assigned: filteredAmendments.filter(a => a.qa_status === 'Assigned'),
    inTesting: filteredAmendments.filter(a => a.qa_status === 'In Testing'),
    failed: filteredAmendments.filter(a => a.qa_status === 'Failed' || a.qa_status === 'Blocked'),
  };

  const getPriorityColor = (priority) => {
    if (priority === 'Critical') return 'text-red-600';
    if (priority === 'High') return 'text-orange-600';
    return 'text-gray-500';
  };

  if (loading) {
    return (
      <div className="flex-1 px-6 py-4">
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-3">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
            <div className="text-gray-500 dark:text-gray-400">Loading QA Dashboard...</div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 px-6 py-4">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 p-6 rounded-lg">
          <div className="flex items-start gap-3">
            <span className="material-symbols-outlined text-2xl">error</span>
            <div className="flex-1">
              <h3 className="font-semibold mb-1">Failed to load QA dashboard</h3>
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

  const KanbanCard = ({ amendment }) => (
    <div
      onClick={() => navigate(`/amendments/${amendment.amendment_id}`)}
      className="bg-white dark:bg-white/5 rounded-xl border border-gray-200 dark:border-white/10 p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer group"
    >
      <div className="flex justify-between items-start mb-3">
        <span className="bg-primary/10 text-primary text-[10px] font-bold px-2 py-1 rounded">
          {amendment.amendment_reference}
        </span>
        <div
          className="w-6 h-6 rounded-full border-2 border-white dark:border-background-dark bg-primary/20 flex items-center justify-center text-[10px] font-bold text-primary"
          title={getEmployeeName(amendment.qa_assigned_id)}
        >
          {getEmployeeInitials(amendment.qa_assigned_id)}
        </div>
      </div>
      <h4 className="font-bold text-sm mb-2 group-hover:text-primary transition-colors line-clamp-2">
        {amendment.description?.substring(0, 60)}{amendment.description?.length > 60 ? '...' : ''}
      </h4>
      <div className="flex flex-wrap gap-2 mb-4">
        {amendment.application && (
          <span className="flex items-center gap-1 text-[11px] text-gray-500 bg-gray-100 dark:bg-white/5 px-2 py-1 rounded">
            <span className="material-symbols-outlined text-[14px]">terminal</span>
            {amendment.application}
          </span>
        )}
        {amendment.force && (
          <span className="flex items-center gap-1 text-[11px] text-gray-500 bg-gray-100 dark:bg-white/5 px-2 py-1 rounded">
            <span className="material-symbols-outlined text-[14px]">map</span>
            {amendment.force}
          </span>
        )}
      </div>
      <div className="flex items-center justify-between border-t border-gray-100 dark:border-white/5 pt-3">
        <span className={`flex items-center gap-1.5 text-[11px] font-semibold ${getPriorityColor(amendment.priority)}`}>
          {amendment.priority === 'Critical' && <span className="material-symbols-outlined text-[16px]">priority_high</span>}
          {amendment.priority}
        </span>
        <span className="material-symbols-outlined text-[18px] text-gray-300">drag_indicator</span>
      </div>
    </div>
  );

  const KanbanColumn = ({ title, items, count, colorClass = 'text-gray-500', bgClass = '' }) => (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between px-2">
        <div className="flex items-center gap-2">
          <h3 className={`font-bold text-sm uppercase tracking-widest ${colorClass}`}>{title}</h3>
          <span className={`${colorClass === 'text-primary' ? 'bg-primary text-white' : colorClass === 'text-red-500' ? 'bg-red-500 text-white' : 'bg-gray-200 dark:bg-white/10 text-gray-600 dark:text-gray-400'} text-[10px] font-bold px-2 py-0.5 rounded-full`}>
            {count}
          </span>
        </div>
      </div>
      <div className={`min-h-[calc(100vh-320px)] flex flex-col gap-3 p-1 ${bgClass}`}>
        {items.map(amendment => (
          <KanbanCard key={amendment.amendment_id} amendment={amendment} />
        ))}
        {items.length === 0 && (
          <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
            No items
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="flex-1 px-6 py-4">
      {/* Tabs & Filters */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div className="flex border-b border-gray-200 dark:border-white/10 gap-6">
          <button className="flex flex-col items-center justify-center border-b-[3px] border-primary pb-3 pt-2">
            <p className="text-sm font-bold text-primary">Board View</p>
          </button>
          <Link to="/amendments" className="flex flex-col items-center justify-center border-b-[3px] border-transparent text-gray-500 pb-3 pt-2 hover:text-primary">
            <p className="text-sm font-bold">List View</p>
          </Link>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-wider mr-2">Filters:</span>
          <select
            value={filters.application}
            onChange={(e) => setFilters({...filters, application: e.target.value})}
            className="h-9 rounded-lg bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 px-3 text-xs font-semibold"
          >
            <option value="all">All Apps</option>
            {applications.map(app => (
              <option key={app.application_id} value={app.application_name}>{app.application_name}</option>
            ))}
          </select>
          <select
            value={filters.priority}
            onChange={(e) => setFilters({...filters, priority: e.target.value})}
            className="h-9 rounded-lg bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 px-3 text-xs font-semibold"
          >
            <option value="all">All Priorities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
          <button
            onClick={() => setFilters({ application: 'all', force: 'all', priority: 'all' })}
            className="h-9 px-3 text-xs font-bold text-primary hover:underline"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Kanban Board */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <KanbanColumn
          title="Not Started"
          items={columns.notStarted}
          count={columns.notStarted.length}
        />
        <KanbanColumn
          title="Assigned"
          items={columns.assigned}
          count={columns.assigned.length}
        />
        <KanbanColumn
          title="In Testing"
          items={columns.inTesting}
          count={columns.inTesting.length}
          colorClass="text-primary"
          bgClass="bg-primary/5 rounded-xl border border-dashed border-primary/20"
        />
        <KanbanColumn
          title="Failed/Blocked"
          items={columns.failed}
          count={columns.failed.length}
          colorClass="text-red-500"
        />
      </div>

      {/* Floating Action Button */}
      <Link
        to="/amendments/new"
        className="fixed bottom-8 right-8 flex items-center gap-2 bg-primary text-white px-6 py-3 rounded-full shadow-xl hover:bg-primary/90 transition-all transform hover:scale-105 active:scale-95 z-50"
      >
        <span className="material-symbols-outlined">add</span>
        <span className="font-bold text-sm">New Amendment</span>
      </Link>
    </div>
  );
};

export default QADashboard;
