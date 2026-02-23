import { useState, useEffect, useMemo, memo } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import type { Project } from '../types';
import { Plus, Search, Activity, X } from 'lucide-react';
import { useDebounce } from '../hooks/useDebounce';

/**
 * Memoized ProjectRow to prevent re-rendering when the search term changes
 * but the project data remains identical.
 */
const ProjectRow = memo(({ project }: { project: Project }) => (
  <tr className="hover:bg-slate-50 transition-colors">
    <td className="px-6 py-4">
      <div className="font-medium text-slate-900">{project.name}</div>
      <div className="text-xs text-slate-500">ID: {project.project_id}</div>
    </td>
    <td className="px-6 py-4">
      <div className="flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${
          project.last_scan_state === 'COMPLETED' ? 'bg-green-500' :
          project.last_scan_state === 'FAILED' ? 'bg-red-500' :
          project.last_scan_state === 'RUNNING' ? 'bg-blue-500 animate-pulse' : 'bg-slate-300'
        }`} />
        <span className="text-sm font-medium text-slate-700">
          {project.last_scan_state || 'No scans yet'}
        </span>
      </div>
    </td>
    <td className="px-6 py-4">
      <Link
        to={`/projects/${project.project_id}`}
        className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center gap-1"
      >
        <Activity className="w-4 h-4" />
        Manage
      </Link>
    </td>
  </tr>
));

ProjectRow.displayName = 'ProjectRow';

const ACTIVE_STATES = new Set(['CREATED', 'QUEUED', 'RUNNING']);

const DashboardPage = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  // Performance: Debounce search input to avoid re-filtering and re-renders on every keystroke
  const debouncedSearchTerm = useDebounce(searchTerm, 300);

  // Performance: Memoize filtered projects to avoid re-calculating on every render.
  // We use debouncedSearchTerm to significantly reduce CPU usage during typing.
  const hasActiveScan = useMemo(
    () => projects.some((p) => ACTIVE_STATES.has(p.last_scan_state ?? '')),
    [projects]
  );

  const filteredProjects = useMemo(() => {
    if (!debouncedSearchTerm) return projects;

    // Performance: Pre-calculate lowercase search term once per update
    const lowerSearch = debouncedSearchTerm.toLowerCase();
    return projects.filter(project =>
      project.name.toLowerCase().includes(lowerSearch)
    );
  }, [projects, debouncedSearchTerm]);

  useEffect(() => {
    api.projects.list().then(data => {
      setProjects(data);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="p-8">Loading projects...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div className="relative w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" aria-hidden="true" />
          <input
            type="text"
            placeholder="Search projects..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            aria-label="Search projects"
            className="w-full pl-10 pr-10 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5 rounded-full hover:bg-slate-100 transition-colors"
              aria-label="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
        <Link
          to="/projects/create"
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Project
        </Link>
      </div>

      {hasActiveScan && (
        <div className="bg-amber-50 border border-amber-200 text-amber-800 rounded-lg px-4 py-3 text-sm">
          A scan is currently active. New scan triggers are temporarily blocked until completion.
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Project Name</th>
              <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Last Scan</th>
              <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {filteredProjects.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-6 py-12 text-center text-slate-500">
                  {debouncedSearchTerm
                    ? `No projects matching "${debouncedSearchTerm}"`
                    : "No projects found. Create one to get started."}
                </td>
              </tr>
            ) : (
              filteredProjects.map(project => (
                <ProjectRow key={project.project_id} project={project} />
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DashboardPage;
