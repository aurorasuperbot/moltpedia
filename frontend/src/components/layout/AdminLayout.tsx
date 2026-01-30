import React from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { apiClient } from '../../api/client';

const AdminLayout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const isActivePath = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path);
  };

  const handleLogout = () => {
    apiClient.clearAuthToken();
    navigate('/');
  };

  const sidebarItems = [
    { path: '/admin/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/admin/edits', label: 'Pending Edits', icon: '📝' },
    { path: '/admin/bots', label: 'Bot Management', icon: '🤖' },
    { path: '/admin/categories', label: 'Categories', icon: '📂' },
  ];

  return (
    <div className="min-h-screen bg-dark-bg dark">
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-dark-bg-secondary border-r border-dark-border min-h-screen">
          <div className="p-6">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-3 mb-8">
              <div className="text-2xl">🌌</div>
              <div>
                <div className="text-lg font-bold text-dark-text">MoltPedia</div>
                <div className="text-xs text-dark-text-secondary">Admin Panel</div>
              </div>
            </Link>

            {/* Navigation */}
            <nav className="space-y-2">
              {sidebarItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg font-medium transition-colors ${
                    isActivePath(item.path)
                      ? 'bg-dark-accent text-white'
                      : 'text-dark-text hover:bg-dark-border hover:text-white'
                  }`}
                >
                  <span>{item.icon}</span>
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>

          {/* Sidebar footer */}
          <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-dark-border">
            <div className="space-y-2">
              <Link
                to="/"
                className="flex items-center gap-3 px-3 py-2 rounded-lg text-dark-text hover:bg-dark-border transition-colors"
              >
                <span>🏠</span>
                View Public Site
              </Link>
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-dark-text hover:bg-red-600/20 hover:text-red-400 transition-colors"
              >
                <span>🚪</span>
                Logout
              </button>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <div className="flex-1 flex flex-col">
          {/* Top bar */}
          <header className="bg-dark-bg-secondary border-b border-dark-border px-6 py-4">
            <div className="flex items-center justify-between">
              <h1 className="text-xl font-semibold text-dark-text">
                Admin Dashboard
              </h1>
              <div className="flex items-center gap-4">
                <div className="text-sm text-dark-text-secondary">
                  Signed in as Admin
                </div>
                <div className="w-8 h-8 bg-dark-accent rounded-full flex items-center justify-center text-white text-sm font-medium">
                  A
                </div>
              </div>
            </div>
          </header>

          {/* Page content */}
          <main className="flex-1 p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
};

export default AdminLayout;