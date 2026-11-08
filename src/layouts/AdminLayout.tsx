import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  Activity,
  ClipboardList,
  ExternalLink,
  Flame,
  LayoutDashboard,
  LogOut,
  Menu,
  Server,
  Settings,
  Shield,
  Users,
  Wrench,
  X,
} from 'lucide-react';
import { useAdminAuth } from '../context/AdminAuthContext';

export const AdminLayout: React.FC = () => {
  const { adminUser, logout } = useAdminAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/admin/login');
  };

  const navItems = [
    { name: 'Overview', to: '/admin', icon: LayoutDashboard, exact: true },
    { name: 'Users', to: '/admin/users', icon: Users },
    { name: 'Community Reports', to: '/admin/reports', icon: ClipboardList },
    { name: 'Threat Intelligence', to: '/admin/threat-intelligence', icon: Flame },
    { name: 'System Monitoring', to: '/admin/system', icon: Server },
    { name: 'Maintenance Mode', to: '/admin/maintenance', icon: Wrench },
    { name: 'Audit Logs', to: '/admin/audit-logs', icon: Activity },
    { name: 'Settings', to: '/admin/settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-[#080808] text-[#F5F5F5] font-sans flex flex-col md:flex-row antialiased">
      {/* ------------------------------------------------------------- */}
      {/* Desktop Sidebar                                               */}
      {/* ------------------------------------------------------------- */}
      <aside className="hidden md:flex flex-col w-64 border-r border-[#222222] bg-[#0C0C0C] shrink-0 sticky top-0 h-screen">
        {/* Brand Header */}
        <div className="p-5 border-b border-[#222222] flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded bg-[#181818] border border-[#333333] flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="text-sm font-semibold tracking-wide flex items-center space-x-1.5">
                <span>TrustGuard</span>
                <span className="text-[10px] font-mono px-1 py-0.2 bg-white text-black font-bold rounded">
                  ADMIN
                </span>
              </div>
              <p className="text-[10px] font-mono text-[#777777]">COMMAND CONSOLE</p>
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.exact}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-3 py-2.5 rounded text-xs font-mono tracking-wider transition-colors ${
                  isActive
                    ? 'bg-[#1D1D1D] text-white border-l-2 border-white pl-2.5 font-semibold'
                    : 'text-[#888888] hover:text-[#E0E0E0] hover:bg-[#141414]'
                }`
              }
            >
              <item.icon className="w-4 h-4 shrink-0" />
              <span>{item.name}</span>
            </NavLink>
          ))}
        </nav>

        {/* Footer Admin Info & Quick Actions */}
        <div className="p-3 border-t border-[#222222] space-y-2 bg-[#0A0A0A]">
          <div className="p-2.5 bg-[#141414] border border-[#222222] rounded flex items-center justify-between">
            <div className="truncate pr-2">
              <p className="text-xs font-mono font-medium text-white truncate">
                {adminUser?.username || 'admin'}
              </p>
              <p className="text-[10px] font-mono text-[#666666] uppercase truncate">
                {adminUser?.role?.replace('_', ' ') || 'Super Admin'}
              </p>
            </div>
            <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" title="Active Admin Session" />
          </div>

          <div className="flex items-center space-x-1">
            <a
              href="/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 flex items-center justify-center space-x-1 py-1.5 px-2 bg-[#141414] hover:bg-[#1E1E1E] text-[#888888] hover:text-white border border-[#222222] rounded text-[11px] font-mono transition-colors"
            >
              <span>Public Site</span>
              <ExternalLink className="w-3 h-3" />
            </a>
            <button
              onClick={handleLogout}
              className="py-1.5 px-2.5 bg-[#141414] hover:bg-rose-950/30 text-rose-400 hover:text-rose-300 border border-[#222222] hover:border-rose-900/50 rounded text-[11px] font-mono flex items-center transition-colors"
              title="Terminate Admin Session"
            >
              <LogOut className="w-3 h-3" />
            </button>
          </div>
        </div>
      </aside>

      {/* ------------------------------------------------------------- */}
      {/* Mobile Top Header                                             */}
      {/* ------------------------------------------------------------- */}
      <header className="md:hidden flex items-center justify-between p-4 border-b border-[#222222] bg-[#0C0C0C] sticky top-0 z-40">
        <div className="flex items-center space-x-2">
          <Shield className="w-4 h-4 text-white" />
          <span className="text-sm font-semibold tracking-wide">TrustGuard AI Admin</span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-1.5 bg-[#161616] border border-[#262626] rounded text-[#888888]"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </header>

      {/* Mobile Navigation Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-[#0C0C0C] border-b border-[#222222] px-4 py-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.exact}
              onClick={() => setMobileMenuOpen(false)}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-3 py-2.5 rounded text-xs font-mono tracking-wider ${
                  isActive
                    ? 'bg-[#1D1D1D] text-white font-semibold'
                    : 'text-[#888888] hover:text-white'
                }`
              }
            >
              <item.icon className="w-4 h-4" />
              <span>{item.name}</span>
            </NavLink>
          ))}
          <button
            onClick={handleLogout}
            className="w-full mt-2 flex items-center space-x-3 px-3 py-2.5 rounded text-xs font-mono text-rose-400 hover:bg-rose-950/20"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout Administrator</span>
          </button>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* Main Administrative Content Area                              */}
      {/* ------------------------------------------------------------- */}
      <main className="flex-1 flex flex-col min-w-0 bg-[#080808] overflow-y-auto">
        <div className="p-6 md:p-8 max-w-7xl mx-auto w-full space-y-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
