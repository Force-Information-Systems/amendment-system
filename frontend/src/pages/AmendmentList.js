import React, { useState, useEffect, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { amendmentAPI, referenceAPI } from '../services/api';

function AmendmentList() {
  const location = useLocation();
  const navigate = useNavigate();

  const getInitialFilters = () => {
    const searchParams = new URLSearchParams(location.search);
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
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statuses, setStatuses] = useState([]);
  const [priorities, setPriorities] = useState([]);
  const [types, setTypes] = useState([]);
  const [developmentStatuses, setDevelopmentStatuses] = useState([]);
  const [filters, setFilters] = useState(getInitialFilters());
  const [pagination, setPagination] = useState({ skip: 0, limit: 25 });

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
      setAmendments(response.data.items || []);
      setTotalCount(response.data.total || response.data.items?.length || 0);
      setError(null);
    } catch (err) {
      setError('Failed to load amendments: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  }, [filters, pagination]);

  useEffect(() => { loadReferenceData(); }, [loadReferenceData]);
  useEffect(() => { loadAmendments(); }, [loadAmendments]);

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
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
    setFilters(prev => ({ ...prev, [field]: value }));
    setPagination(prev => ({ ...prev, skip: 0 }));
  };

  const clearFilters = () => {
    setFilters({
      search_text: '', amendment_status: '', priority: '', amendment_type: '',
      force: '', development_status: '', assigned_to: '', reported_by: '',
      qa_completed: '', database_changes: '', db_upgrade_changes: '',
    });
    setPagination({ skip: 0, limit: 25 });
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const getPriorityClass = (priority) => {
    if (priority === 'Critical') return 'text-red-600 dark:text-red-400';
    if (priority === 'High') return 'text-orange-600 dark:text-orange-400';
    return 'text-gray-500';
  };

  const getRowPriorityClass = (priority) => {
    if (priority === 'Critical') return 'bg-red-50 dark:bg-red-950/20 border-l-4 border-l-red-500';
    if (priority === 'High') return 'bg-orange-50 dark:bg-orange-950/20 border-l-4 border-l-orange-400';
    return 'border-l-4 border-l-transparent';
  };

  return (
    <div className="flex flex-1 flex-col p-6 lg:p-10 max-w-[1400px] mx-auto w-full">
      {/* Page Heading */}
      <div className="flex flex-wrap justify-between items-end gap-3 pb-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-gray-900 dark:text-white text-3xl font-black leading-tight tracking-tight">Software Amendments</h1>
          <p className="text-gray-500 dark:text-gray-400 text-base">Manage faults, enhancements, and suggestions.</p>
        </div>
        <Link
          to="/amendments/new"
          className="flex items-center justify-center rounded-lg h-10 px-4 bg-primary text-white text-sm font-bold transition-all hover:bg-opacity-90"
        >
          <span className="material-symbols-outlined mr-2 text-lg">add</span>
          New Amendment
        </Link>
      </div>

      {/* Filters Ribbon */}
      <div className="flex gap-3 py-4 flex-wrap items-center">
        {/* Search */}
        <div className="flex w-64 items-stretch rounded-lg bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 shadow-sm">
          <div className="flex items-center justify-center pl-3 text-gray-400">
            <span className="material-symbols-outlined text-lg">search</span>
          </div>
          <input
            className="w-full border-none bg-transparent py-2 px-2 text-sm focus:ring-0 placeholder:text-gray-400"
            placeholder="Search..."
            value={filters.search_text}
            onChange={(e) => handleFilterChange('search_text', e.target.value)}
          />
        </div>

        {/* Type Filter */}
        <select
          value={filters.amendment_type}
          onChange={(e) => handleFilterChange('amendment_type', e.target.value)}
          className="h-9 rounded-lg bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 px-3 text-sm font-medium shadow-sm focus:ring-primary"
        >
          <option value="">All Types</option>
          {types.map(type => <option key={type} value={type}>{type}</option>)}
        </select>

        {/* Priority Filter */}
        <select
          value={filters.priority}
          onChange={(e) => handleFilterChange('priority', e.target.value)}
          className="h-9 rounded-lg bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 px-3 text-sm font-medium shadow-sm focus:ring-primary"
        >
          <option value="">All Priorities</option>
          {priorities.map(p => <option key={p} value={p}>{p}</option>)}
        </select>

        {/* Status Filter */}
        <select
          value={filters.amendment_status}
          onChange={(e) => handleFilterChange('amendment_status', e.target.value)}
          className="h-9 rounded-lg bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 px-3 text-sm font-medium shadow-sm focus:ring-primary"
        >
          <option value="">All Statuses</option>
          {statuses.map(s => <option key={s} value={s}>{s}</option>)}
        </select>

        {/* Dev Status Filter */}
        <select
          value={filters.development_status}
          onChange={(e) => handleFilterChange('development_status', e.target.value)}
          className="h-9 rounded-lg bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 px-3 text-sm font-medium shadow-sm focus:ring-primary"
        >
          <option value="">All Dev Status</option>
          {developmentStatuses.map(s => <option key={s} value={s}>{s}</option>)}
        </select>

        <div className="h-6 w-px bg-gray-200 dark:bg-white/10 mx-2" />
        <button onClick={clearFilters} className="text-primary text-sm font-semibold hover:underline">Clear filters</button>
      </div>

      {/* Loading/Error */}
      {loading && (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading amendments...</div>
        </div>
      )}
      {error && <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-4">{error}</div>}

      {!loading && !error && (
        <>
          {/* Main Data Table */}
          <div className="overflow-hidden rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse min-w-[1000px]">
                <thead>
                  <tr className="bg-gray-50 dark:bg-white/5 border-b border-gray-200 dark:border-white/10">
                    <th className="px-6 py-4 text-gray-500 dark:text-gray-400 text-xs font-bold uppercase tracking-wider w-32">Ref</th>
                    <th className="px-6 py-4 text-gray-500 dark:text-gray-400 text-xs font-bold uppercase tracking-wider">Title</th>
                    <th className="px-6 py-4 text-gray-500 dark:text-gray-400 text-xs font-bold uppercase tracking-wider w-28">Type</th>
                    <th className="px-6 py-4 text-gray-500 dark:text-gray-400 text-xs font-bold uppercase tracking-wider w-28">Priority</th>
                    <th className="px-6 py-4 text-gray-500 dark:text-gray-400 text-xs font-bold uppercase tracking-wider w-36">Status</th>
                    <th className="px-6 py-4 text-gray-500 dark:text-gray-400 text-xs font-bold uppercase tracking-wider w-32">Assigned</th>
                    <th className="px-6 py-4 text-gray-500 dark:text-gray-400 text-xs font-bold uppercase tracking-wider w-28">QA</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-white/10">
                  {amendments.length === 0 ? (
                    <tr>
                      <td colSpan="7" className="px-6 py-12 text-center text-gray-500">No amendments found</td>
                    </tr>
                  ) : (
                    amendments.map(amendment => (
                      <tr
                        key={amendment.amendment_id}
                        className={`${getRowPriorityClass(amendment.priority)} hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer group`}
                        onClick={() => navigate(`/amendments/${amendment.amendment_id}`)}
                      >
                        <td className="px-6 py-4 font-mono text-sm font-bold text-primary">{amendment.amendment_reference}</td>
                        <td className="px-6 py-4">
                          <div className="flex flex-col">
                            <span className="text-gray-900 dark:text-white text-sm font-semibold group-hover:text-primary transition-colors">
                              {amendment.description?.substring(0, 60)}{amendment.description?.length > 60 ? '...' : ''}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs font-medium">
                            {amendment.amendment_type}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`flex items-center gap-1 text-xs font-bold ${getPriorityClass(amendment.priority)}`}>
                            {amendment.priority === 'Critical' && <span className="material-symbols-outlined text-sm">priority_high</span>}
                            {amendment.priority === 'High' && <span className="material-symbols-outlined text-sm">keyboard_double_arrow_up</span>}
                            {amendment.priority}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`status-badge status-${amendment.amendment_status?.toLowerCase().replace(' ', '-')}`}>
                            {amendment.amendment_status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm">{amendment.assigned_to || '-'}</td>
                        <td className="px-6 py-4">
                          {amendment.qa_completed ? (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              <span className="material-symbols-outlined text-sm mr-1">check</span> Done
                            </span>
                          ) : amendment.qa_assigned_id ? (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                              In QA
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between px-6 py-4 bg-gray-50 dark:bg-white/5 border-t border-gray-200 dark:border-white/10">
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <span>Showing {pagination.skip + 1} to {pagination.skip + amendments.length} of {totalCount} results</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPagination(prev => ({ ...prev, skip: Math.max(0, prev.skip - prev.limit) }))}
                  disabled={pagination.skip === 0}
                  className="p-1 rounded hover:bg-gray-200 dark:hover:bg-white/10 text-gray-500 disabled:opacity-30"
                >
                  <span className="material-symbols-outlined">chevron_left</span>
                </button>
                <button
                  onClick={() => setPagination(prev => ({ ...prev, skip: prev.skip + prev.limit }))}
                  disabled={amendments.length < pagination.limit}
                  className="p-1 rounded hover:bg-gray-200 dark:hover:bg-white/10 text-gray-900 dark:text-white disabled:opacity-30"
                >
                  <span className="material-symbols-outlined">chevron_right</span>
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default AmendmentList;
