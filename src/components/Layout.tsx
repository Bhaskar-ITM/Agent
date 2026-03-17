import { useState, useEffect } from 'react';
import { Outlet, Link, useNavigate, useLocation, useParams } from 'react-router-dom';
import { Shield, LayoutDashboard, PlusCircle, LogOut, Menu, X, Activity, History, Settings, Key } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../hooks/useAuth';
import { Breadcrumbs } from './Breadcrumbs';
import { api } from '../services/api';

const Layout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { projectId, scanId } = useParams();
  const { logout } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Fetch scan context if scanId is present
  const { data: scanData } = useQuery({
    queryKey: ['scan', scanId],
    queryFn: () => scanId ? api.scans.get(scanId) : null,
    enabled: !!scanId,
    retry: false,
  });

  // Determine active project ID
  const activeProjectId = projectId || scanData?.project_id;

  // Fetch project context using React Query
  const { data: projectData } = useQuery({
    queryKey: ['project', activeProjectId],
    queryFn: () => activeProjectId ? api.projects.get(activeProjectId) : null,
    enabled: !!activeProjectId,
    retry: false,
  });

  const currentProject = projectData ? { id: projectData.project_id, name: projectData.name } : undefined;

  // Close mobile menu on any navigation
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path: string) => location.pathname === path;
  const showProjectContext = currentProject !== undefined;

  const NavLink = ({ to, icon: Icon, children }: { to: string; icon: any; children: React.ReactNode }) => (
    <Link
      to={to}
      onClick={() => setIsMobileMenuOpen(false)}
      className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${
        isActive(to) 
          ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20' 
          : 'text-slate-400 hover:bg-slate-800 hover:text-white'
      }`}
    >
      <Icon className={`w-5 h-5 ${isActive(to) ? 'text-white' : 'group-hover:text-blue-400 transition-colors'}`} />
      <span className="font-bold text-sm tracking-tight">{children}</span>
    </Link>
  );

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row">
      {/* Mobile Header */}
      <header className="md:hidden h-16 bg-slate-900 text-white flex items-center justify-between px-6 sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <Shield className="w-7 h-7 text-blue-400" />
          <span className="font-bold tracking-tight">DevSecOps</span>
        </div>
        <button 
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
        >
          {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </header>

      {/* Sidebar Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-40 md:hidden animate-in fade-in duration-300"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 md:relative md:translate-x-0 transition-transform duration-500 ease-in-out
        w-[280px] md:w-72 bg-slate-900 text-slate-100 flex flex-col border-r border-slate-800 shadow-2xl md:shadow-none
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="p-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-900/40">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-black tracking-tight leading-none">PIPELINE</span>
              <span className="text-[10px] font-bold text-blue-400 uppercase tracking-[0.2em] mt-1">Control Plane</span>
            </div>
          </div>
          <button 
            onClick={() => setIsMobileMenuOpen(false)}
            className="md:hidden p-2 text-slate-500 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 px-6 py-4 space-y-8 overflow-y-auto">
          {/* Main Navigation */}
          <div>
            <h3 className="px-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Core</h3>
            <div className="space-y-1">
              <NavLink to="/dashboard" icon={LayoutDashboard}>Dashboard</NavLink>
              <NavLink to="/projects/create" icon={PlusCircle}>New Project</NavLink>
              <NavLink to="/users" icon={Shield}>Users</NavLink>
              <NavLink to="/settings" icon={Key}>API Settings</NavLink>
            </div>
          </div>

          {/* Contextual Project Navigation */}
          {showProjectContext && (
            <div className="animate-in fade-in slide-in-from-left-4 duration-500">
              <h3 className="px-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 flex items-center justify-between">
                <span>Active Project</span>
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></span>
              </h3>
              <div className="bg-slate-800/40 rounded-2xl p-2 border border-slate-800">
                <div className="px-4 py-3 border-b border-slate-800 mb-2">
                  <div className="font-bold text-sm truncate text-white">{currentProject?.name || 'Loading...'}</div>
                  <div className="text-[10px] font-medium text-slate-500 font-mono mt-0.5 truncate">{currentProject?.id}</div>
                </div>
                <div className="space-y-1">
                  <NavLink to={`/projects/${currentProject?.id}`} icon={Activity}>Controls</NavLink>
                  <NavLink to={`/projects/${currentProject?.id}/history`} icon={History}>Scan History</NavLink>
                  <NavLink to={`/projects/${currentProject?.id}/manual`} icon={Settings}>Configure</NavLink>
                </div>
              </div>
            </div>
          )}
        </nav>

        <div className="p-6 mt-auto">
          <div className="bg-slate-800/50 rounded-2xl p-4 mb-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-slate-700 to-slate-800 rounded-xl flex items-center justify-center font-black text-slate-300 border border-slate-700 shadow-inner">
              A
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-bold truncate text-white">Admin User</div>
              <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">System Operator</div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 w-full rounded-xl text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-all duration-200 group"
          >
            <LogOut className="w-5 h-5 group-hover:scale-110 transition-transform" />
            <span className="font-bold text-sm tracking-tight text-left">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        <header className="h-20 bg-white border-b border-slate-200 flex items-center justify-between px-8 flex-shrink-0 relative z-30 shadow-sm shadow-slate-100/50">
          <div className="flex flex-col">
            <h1 className="text-slate-900 font-black text-xl tracking-tight leading-none mb-1">
              {location.pathname === '/dashboard' ? 'Project Dashboard' :
               location.pathname === '/projects/create' ? 'Create Project' :
               location.pathname.includes('/projects/') && location.pathname.includes('/edit') ? 'Edit Project' :
               location.pathname.includes('/projects/') && location.pathname.includes('/manual') ? 'Scan Configuration' :
               location.pathname.includes('/projects/') && location.pathname.includes('/history') ? 'Scan History' :
               location.pathname.includes('/projects/') ? 'Project Controls' :
               location.pathname.includes('/scans/') ? 'Scan Details' :
               location.pathname.includes('/history') ? 'Scan Archive' :
               location.pathname.includes('/login') || location.pathname.includes('/register') ? '' : 'Project Control'}
            </h1>
            {!(location.pathname.includes('/login') || location.pathname.includes('/register')) && (
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">System Operational</span>
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-6">
            <div className="hidden lg:flex flex-col items-end">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Server Time</span>
              <span className="text-xs font-bold text-slate-700 font-mono tracking-tighter">
                {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })} UTC
              </span>
            </div>
            <div className="w-px h-8 bg-slate-200"></div>
            <button className="relative p-2 text-slate-400 hover:text-slate-600 transition-colors">
              <Activity className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-500 rounded-full border-2 border-white"></span>
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto bg-slate-50/50 relative">
          <div className="max-w-[1600px] mx-auto p-8">
            <Breadcrumbs projectName={currentProject?.name} />
            <div className="animate-in fade-in duration-700 slide-in-from-bottom-2">
              <Outlet />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Layout;
