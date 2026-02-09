import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { amendmentAPI } from '../services/api';

function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [recentAmendments, setRecentAmendments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [statsResponse, amendmentsResponse] = await Promise.all([
        amendmentAPI.getStats(),
        amendmentAPI.getAll({ limit: 5, priority: 'Critical' }),
      ]);
      setStats(statsResponse.data);
      setRecentAmendments(amendmentsResponse.data?.items || []);
      setError(null);
    } catch (err) {
      setError('Failed to load statistics: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-[1400px] mx-auto p-6 lg:px-10">
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-3">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
            <div className="text-gray-500 dark:text-gray-400">Loading dashboard...</div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-[1400px] mx-auto p-6 lg:px-10">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 p-6 rounded-lg">
          <div className="flex items-start gap-3">
            <span className="material-symbols-outlined text-2xl">error</span>
            <div className="flex-1">
              <h3 className="font-semibold mb-1">Failed to load dashboard</h3>
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

  const getPriorityIcon = (priority) => {
    if (priority === 'Critical') return 'priority_high';
    if (priority === 'High') return 'keyboard_double_arrow_up';
    return null;
  };

  const getPriorityClass = (priority) => {
    if (priority === 'Critical') return 'text-red-500';
    if (priority === 'High') return 'text-orange-500';
    return 'text-gray-500';
  };

  return (
    <div className="max-w-[1400px] mx-auto p-6 lg:px-10">
      {/* Welcome Section */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Global Overview</h1>
        <p className="text-gray-500 text-sm">Real-time status of software amendments and quality assurance.</p>
      </div>

      {/* KPI Cards Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {/* Active Amendments */}
        <Link to="/amendments" className="flex flex-col gap-2 rounded-xl p-5 border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start">
            <p className="text-gray-500 dark:text-gray-400 text-xs font-bold uppercase tracking-wider">Total Amendments</p>
            <span className="material-symbols-outlined text-primary">edit_note</span>
          </div>
          <p className="text-gray-900 dark:text-white tracking-tight text-3xl font-bold leading-tight">{stats?.total_amendments || 0}</p>
          <div className="flex items-center gap-1">
            <span className="text-green-600 text-sm font-bold">Active</span>
          </div>
        </Link>

        {/* Failed QA */}
        <Link to="/amendments?qa_status=Failed" className="flex flex-col gap-2 rounded-xl p-5 border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 shadow-sm hover:shadow-md transition-shadow border-l-4 border-l-red-500">
          <div className="flex justify-between items-start">
            <p className="text-gray-500 dark:text-gray-400 text-xs font-bold uppercase tracking-wider">Failed QA</p>
            <span className="material-symbols-outlined text-red-500">error</span>
          </div>
          <p className="text-gray-900 dark:text-white tracking-tight text-3xl font-bold leading-tight">
            {stats?.by_status?.['Failed'] || 0}
          </p>
          <div className="flex items-center gap-1">
            <span className="text-red-500 text-sm font-bold">Requires review</span>
          </div>
        </Link>

        {/* In Testing */}
        <Link to="/amendments?amendment_status=Testing" className="flex flex-col gap-2 rounded-xl p-5 border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 shadow-sm hover:shadow-md transition-shadow border-l-4 border-l-orange-400">
          <div className="flex justify-between items-start">
            <p className="text-gray-500 dark:text-gray-400 text-xs font-bold uppercase tracking-wider">In Testing</p>
            <span className="material-symbols-outlined text-orange-400">science</span>
          </div>
          <p className="text-gray-900 dark:text-white tracking-tight text-3xl font-bold leading-tight">
            {stats?.by_status?.['Testing'] || 0}
          </p>
          <div className="flex items-center gap-1">
            <span className="text-orange-500 text-sm font-bold">QA in progress</span>
          </div>
        </Link>

        {/* QA Completed */}
        <Link to="/amendments?qa_completed=true" className="flex flex-col gap-2 rounded-xl p-5 border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start">
            <p className="text-gray-500 dark:text-gray-400 text-xs font-bold uppercase tracking-wider">QA Completed</p>
            <span className="material-symbols-outlined text-green-500">verified</span>
          </div>
          <p className="text-gray-900 dark:text-white tracking-tight text-3xl font-bold leading-tight">{stats?.qa_completed || 0}</p>
          <div className="flex items-center gap-1">
            <span className="text-green-600 text-sm font-bold">Approved</span>
          </div>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Charts Section (Left 2/3) */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          {/* Status Distribution */}
          <div className="rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 p-6 shadow-sm">
            <h3 className="text-gray-900 dark:text-white text-lg font-bold mb-6">Status Distribution</h3>
            <div className="flex flex-col gap-4">
              {stats?.by_status && Object.entries(stats.by_status).map(([status, count]) => {
                const total = stats.total_amendments || 1;
                const percentage = ((count / total) * 100).toFixed(1);
                const getStatusColor = (s) => {
                  if (s === 'Completed' || s === 'Deployed') return 'bg-green-500';
                  if (s === 'Testing') return 'bg-purple-500';
                  if (s === 'In Progress') return 'bg-blue-500';
                  if (s === 'Open') return 'bg-primary';
                  return 'bg-gray-400';
                };
                return (
                  <div key={status} className="space-y-1">
                    <div className="flex justify-between text-xs font-bold text-gray-500 dark:text-gray-400">
                      <span className="uppercase">{status}</span>
                      <span>{count} ({percentage}%)</span>
                    </div>
                    <div className="w-full h-3 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                      <div className={`${getStatusColor(status)} h-full rounded-full transition-all`} style={{ width: `${percentage}%` }}></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Priority Distribution */}
          <div className="rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 p-6 shadow-sm">
            <h3 className="text-gray-900 dark:text-white text-lg font-bold mb-6">Priority Distribution</h3>
            <div className="flex flex-col gap-4">
              {stats?.by_priority && Object.entries(stats.by_priority).map(([priority, count]) => {
                const total = stats.total_amendments || 1;
                const percentage = ((count / total) * 100).toFixed(1);
                const getPriorityColor = (p) => {
                  if (p === 'Critical') return 'bg-red-500';
                  if (p === 'High') return 'bg-orange-500';
                  if (p === 'Medium') return 'bg-primary';
                  return 'bg-gray-400';
                };
                return (
                  <div key={priority} className="space-y-1">
                    <div className="flex justify-between text-xs font-bold text-gray-500 dark:text-gray-400">
                      <span className="uppercase">{priority}</span>
                      <span>{count} ({percentage}%)</span>
                    </div>
                    <div className="w-full h-3 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                      <div className={`${getPriorityColor(priority)} h-full rounded-full transition-all`} style={{ width: `${percentage}%` }}></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Activity Sidebar (Right 1/3) */}
        <div className="flex flex-col gap-6">
          <div className="rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 p-6 shadow-sm h-full">
            <h3 className="text-gray-900 dark:text-white text-lg font-bold mb-6">By Type</h3>
            <div className="space-y-4">
              {stats?.by_type && Object.entries(stats.by_type).map(([type, count]) => (
                <Link
                  key={type}
                  to={`/amendments?amendment_type=${encodeURIComponent(type)}`}
                  className="flex justify-between items-center p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      type === 'Fault' ? 'bg-red-100 text-red-600' :
                      type === 'Enhancement' ? 'bg-blue-100 text-blue-600' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      <span className="material-symbols-outlined text-base">
                        {type === 'Fault' ? 'bug_report' : type === 'Enhancement' ? 'add_circle' : 'lightbulb'}
                      </span>
                    </div>
                    <span className="text-sm font-medium">{type}</span>
                  </div>
                  <span className="text-sm font-bold text-gray-900 dark:text-white">{count}</span>
                </Link>
              ))}
            </div>
            <Link
              to="/amendments"
              className="w-full mt-6 py-2 text-xs font-bold text-primary bg-primary/10 hover:bg-primary hover:text-white transition-all rounded-lg block text-center"
            >
              View All Amendments
            </Link>
          </div>
        </div>
      </div>

      {/* Critical Amendments Table */}
      <div className="rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 shadow-sm overflow-hidden mb-8">
        <div className="p-6 border-b border-gray-200 dark:border-white/10 flex flex-wrap justify-between items-center gap-4">
          <h3 className="text-gray-900 dark:text-white text-lg font-bold">Critical Amendments Needing Attention</h3>
          <div className="flex gap-2">
            <Link
              to="/amendments/new"
              className="px-4 py-2 bg-primary text-white text-xs font-bold rounded-lg flex items-center gap-2 hover:bg-primary/90 transition-colors"
            >
              <span className="material-symbols-outlined text-lg">add</span>
              New Amendment
            </Link>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-50 dark:bg-white/5 text-gray-500 dark:text-gray-400 text-xs uppercase tracking-wider">
              <tr>
                <th className="px-6 py-4 font-bold">Ref ID</th>
                <th className="px-6 py-4 font-bold">Description</th>
                <th className="px-6 py-4 font-bold">Type</th>
                <th className="px-6 py-4 font-bold">Priority</th>
                <th className="px-6 py-4 font-bold">Status</th>
                <th className="px-6 py-4 font-bold">Assigned To</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-white/10 text-sm">
              {recentAmendments.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                    No critical amendments found
                  </td>
                </tr>
              ) : (
                recentAmendments.map(amendment => (
                  <tr
                    key={amendment.amendment_id}
                    className="hover:bg-primary/5 transition-colors cursor-pointer"
                    onClick={() => navigate(`/amendments/${amendment.amendment_id}`)}
                  >
                    <td className="px-6 py-4 font-bold text-primary">{amendment.amendment_reference}</td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col">
                        <span className="font-bold text-gray-900 dark:text-white">
                          {amendment.description?.substring(0, 50)}{amendment.description?.length > 50 ? '...' : ''}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="bg-gray-100 dark:bg-white/5 px-2 py-1 rounded text-xs font-bold">
                        {amendment.amendment_type}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`flex items-center gap-1 ${getPriorityClass(amendment.priority)} font-bold`}>
                        {getPriorityIcon(amendment.priority) && (
                          <span className="material-symbols-outlined text-base">{getPriorityIcon(amendment.priority)}</span>
                        )}
                        {amendment.priority}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`status-badge status-${amendment.amendment_status?.toLowerCase().replace(' ', '-')}`}>
                        {amendment.amendment_status}
                      </span>
                    </td>
                    <td className="px-6 py-4">{amendment.assigned_to || '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="p-4 bg-gray-50 dark:bg-white/5 border-t border-gray-200 dark:border-white/10 flex justify-center">
          <Link to="/amendments?priority=Critical" className="text-xs font-bold text-primary hover:underline">
            View All Critical Amendments
          </Link>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
