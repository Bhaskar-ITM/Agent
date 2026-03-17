import { useState, useMemo, memo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import type { Project } from '../types';
import { Plus, Search, Activity, X, Trash2, AlertCircle, FolderOpen } from 'lucide-react';
import { useDebounce } from '../hooks/useDebounce';
import { useToast } from '../components/Toast';
import { ConfirmModal } from '../components/ConfirmModal';

// State → badge colour + link hint
const SCAN_STATE_META: Record<
  string,
  { dot: string; label: string; clickable: boolean }
> = {
  COMPLETED: { dot: 'bg-emerald-500', label: 'Completed', clickable: true },
  FAILED:    { dot: 'bg-red-500',     label: 'Failed',    clickable: true },
  RUNNING:   { dot: 'bg-blue-500 animate-pulse', label: 'Running', clickable: true },
  QUEUED:    { dot: 'bg-amber-400 animate-pulse', label: 'Queued', clickable: true },
  CREATED:   { dot: 'bg-slate-300',  label: 'Created',   clickable: false },
  CANCELLED: { dot: 'bg-slate-400',  label: 'Cancelled', clickable: false },
};

const ProjectRow = memo(({ project }: { project: Project }) => {
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const deleteProjectMutation = useMutation({
    mutationFn: () => api.projects.delete(project.project_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setShowDeleteModal(false);
      success('Project deleted', `"${project.name}" has been removed.`);
    },
    onError: () => {
      toastError('Delete failed', 'Could not delete the project. Please try again.');
    },
  });

  const stateMeta = SCAN_STATE_META[project.last_scan_state ?? ''];
  const navigate = useNavigate();

  return (
    <>
      <tr className="hover:bg-slate-50 transition-colors group">
        <td className="px-6 py-4">
          <Link to={`/projects/${project.project_id}`} className="group/name">
            <div className="font-medium text-slate-900 group-hover/name:text-blue-600 transition-colors">
              {project.name}
            </div>
            <div className="text-xs text-slate-400 font-mono mt-0.5">
              {project.project_id.slice(0, 8)}…
            </div>
          </Link>
        </td>

        <td className="px-6 py-4">
          {stateMeta ? (
            stateMeta.clickable ? (
              <button
                onClick={() => navigate(`/projects/${project.project_id}/history`)}
                className="flex items-center gap-2 group/badge hover:opacity-80 transition-opacity"
                title="View scan history"
              >
                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${stateMeta.dot}`} />
                <span className="text-sm font-medium text-slate-700 group-hover/badge:underline">
                  {stateMeta.label}
                </span>
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${stateMeta.dot}`} />
                <span className="text-sm font-medium text-slate-500">{stateMeta.label}</span>
              </div>
            )
          ) : (
            <span className="text-sm text-slate-400">No scans yet</span>
          )}
        </td>

        <td className="px-6 py-4">
          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
            <Link
              to={`/projects/${project.project_id}`}
              className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 px-2.5 py-1.5 rounded-lg hover:bg-blue-50 transition-colors"
            >
              <Activity className="w-3.5 h-3.5" />
              Manage
            </Link>
            <button
              onClick={() => setShowDeleteModal(true)}
              className="inline-flex items-center gap-1.5 text-sm font-medium text-red-600 hover:text-red-700 px-2.5 py-1.5 rounded-lg hover:bg-red-50 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Delete
            </button>
          </div>
        </td>
      </tr>

      <ConfirmModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={() => deleteProjectMutation.mutate()}
        isLoading={deleteProjectMutation.isPending}
        variant="danger"
        title="Delete Project"
        description={
          <>
            Are you sure you want to delete{' '}
            <span className="font-semibold text-slate-900">"{project.name}"</span>?
            This will permanently remove the project and all associated scan records.
            This action cannot be undone.
          </>
        }
        confirmLabel="Yes, delete"
        cancelLabel="Keep project"
      />
    </>
  );
});
ProjectRow.displayName = 'ProjectRow';

const ACTIVE_STATES = new Set(['CREATED', 'QUEUED', 'RUNNING']);

const DashboardPage = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: api.projects.list,
    refetchInterval: 10_000,
  });

  const debouncedSearchTerm = useDebounce(searchTerm, 300);

  const hasActiveScan = useMemo(
    () => projects.some(p => ACTIVE_STATES.has(p.last_scan_state ?? '')),
    [projects]
  );

  const filteredProjects = useMemo(() => {
    if (!debouncedSearchTerm) return projects;
    const lower = debouncedSearchTerm.toLowerCase();
    return projects.filter(p => p.name.toLowerCase().includes(lower));
  }, [projects, debouncedSearchTerm]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div className="h-10 w-72 bg-slate-200 rounded-lg animate-pulse" />
          <div className="h-10 w-32 bg-slate-200 rounded-lg animate-pulse" />
        </div>
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="px-6 py-4 border-b border-slate-100 flex gap-6">
              <div className="flex-1 space-y-2">
                <div className="h-4 w-40 bg-slate-200 rounded animate-pulse" />
                <div className="h-3 w-24 bg-slate-100 rounded animate-pulse" />
              </div>
              <div className="h-4 w-20 bg-slate-200 rounded animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Toolbar */}
      <div className="flex justify-between items-center gap-4">
        <div className="relative w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search projects…"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            aria-label="Search projects"
            className="w-full pl-10 pr-10 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
          />
          {searchTerm && (
            <button
              type="button"
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
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" />
          New Project
        </Link>
      </div>

      {hasActiveScan && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 rounded-lg px-4 py-3 text-sm flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse flex-shrink-0" />
          A scan is currently active. New scan triggers are temporarily blocked until it completes.
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Project</th>
              <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Last Scan</th>
              <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filteredProjects.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-6 py-16 text-center">
                  {debouncedSearchTerm ? (
                    <div className="flex flex-col items-center gap-3">
                      <Search className="w-10 h-10 text-slate-300" />
                      <p className="text-slate-500 font-medium">
                        No projects matching "{debouncedSearchTerm}"
                      </p>
                      <button
                        onClick={() => setSearchTerm('')}
                        className="text-blue-600 hover:underline text-sm"
                      >
                        Clear search
                      </button>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center gap-4">
                      <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center">
                        <FolderOpen className="w-8 h-8 text-slate-400" />
                      </div>
                      <div>
                        <p className="text-slate-700 font-semibold mb-1">No projects yet</p>
                        <p className="text-slate-400 text-sm">Create your first project to start running security scans.</p>
                      </div>
                      <Link
                        to="/projects/create"
                        className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                      >
                        <Plus className="w-4 h-4" />
                        Create your first project
                      </Link>
                    </div>
                  )}
                </td>
              </tr>
            ) : (
              filteredProjects.map(project => (
                <ProjectRow key={project.project_id} project={project} />
              ))
            )}
          </tbody>
        </table>

        {filteredProjects.length > 0 && (
          <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 text-xs text-slate-400">
            {filteredProjects.length} project{filteredProjects.length !== 1 ? 's' : ''}
            {debouncedSearchTerm ? ` matching "${debouncedSearchTerm}"` : ''}
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
