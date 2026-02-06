import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function Layout({ children }) {
  const location = useLocation();
  const { user, logout, isAdmin } = useAuth();

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  return (
    <div className="min-h-screen bg-background-light dark:bg-background-dark text-gray-900 dark:text-white">
      {/* Top Navigation Bar */}
      <header className="flex items-center justify-between whitespace-nowrap border-b border-gray-200 dark:border-white/10 bg-white dark:bg-background-dark px-6 lg:px-10 py-3 sticky top-0 z-50">
        <div className="flex items-center gap-8">
          {/* Logo */}
          <Link to="/dashboard" className="flex items-center gap-3 text-gray-900 dark:text-white">
            <div className="size-8 bg-primary rounded-lg flex items-center justify-center text-white">
              <span className="material-symbols-outlined text-xl">shield</span>
            </div>
            <h2 className="text-lg font-bold leading-tight tracking-tight">Amendment System</h2>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            <Link
              to="/dashboard"
              className={`text-sm font-medium transition-colors ${
                isActive('/dashboard')
                  ? 'text-primary font-bold border-b-2 border-primary pb-1'
                  : 'text-gray-500 dark:text-gray-400 hover:text-primary'
              }`}
            >
              Dashboard
            </Link>
            <Link
              to="/amendments"
              className={`text-sm font-medium transition-colors ${
                isActive('/amendments')
                  ? 'text-primary font-bold border-b-2 border-primary pb-1'
                  : 'text-gray-500 dark:text-gray-400 hover:text-primary'
              }`}
            >
              Amendments
            </Link>
            <Link
              to="/qa-dashboard"
              className={`text-sm font-medium transition-colors ${
                isActive('/qa-dashboard')
                  ? 'text-primary font-bold border-b-2 border-primary pb-1'
                  : 'text-gray-500 dark:text-gray-400 hover:text-primary'
              }`}
            >
              QA Testing
            </Link>
            {isAdmin() && (
              <Link
                to="/admin"
                className={`text-sm font-medium transition-colors ${
                  isActive('/admin')
                    ? 'text-primary font-bold border-b-2 border-primary pb-1'
                    : 'text-gray-500 dark:text-gray-400 hover:text-primary'
                }`}
              >
                Admin
              </Link>
            )}
          </nav>
        </div>

        {/* Right side - Search, Notifications, User */}
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="hidden lg:flex w-64 items-stretch rounded-lg bg-gray-100 dark:bg-white/5 border border-transparent focus-within:border-primary">
            <div className="flex items-center justify-center pl-3 text-gray-400">
              <span className="material-symbols-outlined text-xl">search</span>
            </div>
            <input
              className="w-full border-none bg-transparent py-2 px-2 text-sm focus:ring-0 placeholder:text-gray-400"
              placeholder="Search amendments..."
            />
          </div>

          {/* Notification & Settings buttons */}
          <div className="flex gap-2">
            <button className="relative flex items-center justify-center rounded-lg size-10 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 transition-colors text-white">
              <span className="material-symbols-outlined">notifications</span>
            </button>
            <button className="flex items-center justify-center rounded-lg size-10 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 transition-colors text-white">
              <span className="material-symbols-outlined">settings</span>
            </button>
          </div>

          {/* Divider */}
          <div className="h-8 w-px bg-gray-200 dark:bg-white/10 mx-2" />

          {/* User Info */}
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-bold leading-none text-white">{user?.employee_name || 'User'}</p>
              <p className="text-[11px] text-white mt-1">{user?.role || 'User'}</p>
            </div>
            <div className="size-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold text-sm border-2 border-primary/20">
              {getInitials(user?.employee_name)}
            </div>
            <button
              onClick={logout}
              className="ml-2 text-white hover:text-red-400 transition-colors"
              title="Logout"
            >
              <span className="material-symbols-outlined">logout</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="min-h-[calc(100vh-130px)]">
        {children}
      </main>

      {/* Footer Status Bar */}
      <footer className="bg-white dark:bg-background-dark border-t border-gray-200 dark:border-white/10 px-6 py-2 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            <span className="text-[10px] font-bold text-gray-500 uppercase">Systems Operational</span>
          </div>
        </div>
        <div className="text-[10px] text-gray-500">
          Amendment System v1.0.0
        </div>
      </footer>
    </div>
  );
}

export default Layout;
