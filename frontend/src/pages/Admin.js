import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';

function Admin() {
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const navItems = [
    { path: '/admin/employees', label: 'Employees', icon: 'badge' },
    { path: '/admin/applications', label: 'Applications', icon: 'terminal' },
    { path: '/admin/versions', label: 'Versions', icon: 'history' },
    { path: '/admin/reference', label: 'Reference Data', icon: 'settings' },
  ];

  return (
    <div className="flex h-[calc(100vh-64px)]">
      {/* Side Navigation Bar */}
      <aside className="w-64 flex-shrink-0 flex flex-col bg-white dark:bg-background-dark border-r border-gray-200 dark:border-white/10">
        <div className="p-6 flex flex-col gap-1">
          <h1 className="text-primary text-xl font-black leading-tight tracking-tight uppercase">Admin Panel</h1>
          <p className="text-gray-500 text-xs font-bold uppercase tracking-wider">System Management</p>
        </div>

        <nav className="flex-1 px-4 py-4 space-y-1">
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                isActive(item.path)
                  ? 'bg-primary/10 text-primary border border-primary/20'
                  : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-white/5'
              }`}
            >
              <span className="material-symbols-outlined">{item.icon}</span>
              <span className={`text-sm ${isActive(item.path) ? 'font-bold' : 'font-medium'}`}>{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-100 dark:border-white/10">
          <Link
            to="/dashboard"
            className="w-full flex items-center justify-center gap-2 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 text-sm font-bold py-3 rounded-lg transition-all"
          >
            <span className="material-symbols-outlined text-[20px]">arrow_back</span>
            <span>Back to Dashboard</span>
          </Link>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-y-auto">
        <div className="p-8 max-w-[1200px] mx-auto w-full">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

export default Admin;
