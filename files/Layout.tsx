import { Outlet, Link, useNavigate, useLocation, useParams } from 'react-router-dom';
import { Shield, LayoutDashboard, PlusCircle, LogOut } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

function usePageTitle(): string {
  const location = useLocation();
  const path = location.pathname;

  if (path === '/dashboard')                    return 'Project Dashboard';
  if (path === '/projects/create')              return 'Create New Project';
  if (/^\/projects\/[^/]+\/edit$/.test(path))  return 'Edit Project';
  if (/^\/projects\/[^/]+\/manual$/.test(path)) return 'Manual Scan Configuration';
  if (/^\/projects\/[^/]+\/history$/.test(path)) return 'Scan History';
  if (/^\/projects\/[^/]+$/.test(path))         return 'Project Details';
  if (/^\/scans\/[^/]+$/.test(path))            return 'Scan Status';
  return 'DevSecOps Platform';
}

const Layout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout } = useAuth();
  const pageTitle = usePageTitle();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-100 flex flex-col flex-shrink-0">
        <div className="p-6 flex items-center gap-3 border-b border-slate-800">
          <Shield className="w-7 h-7 text-blue-400 flex-shrink-0" />
          <span className="text-lg font-bold tracking-tight">DevSecOps</span>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-0.5">
          <Link
            to="/dashboard"
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
              isActive('/dashboard')
                ? 'bg-blue-600 text-white font-medium'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
            }`}
          >
            <LayoutDashboard className="w-4 h-4 flex-shrink-0" />
            Dashboard
          </Link>
          <Link
            to="/projects/create"
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
              isActive('/projects/create')
                ? 'bg-blue-600 text-white font-medium'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
            }`}
          >
            <PlusCircle className="w-4 h-4 flex-shrink-0" />
            Create Project
          </Link>
        </nav>

        <div className="p-3 border-t border-slate-800">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 w-full rounded-lg text-sm text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          >
            <LogOut className="w-4 h-4 flex-shrink-0" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto min-w-0">
        <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-8 sticky top-0 z-10 shadow-sm">
          <h1 className="text-slate-800 font-semibold text-base">{pageTitle}</h1>
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <span className="hidden sm:block">Admin</span>
            <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-xs">
              A
            </div>
          </div>
        </header>
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
