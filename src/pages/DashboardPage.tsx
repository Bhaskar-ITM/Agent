import { useState, useMemo, memo, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../services/api";
import type { Project } from "../types";
import {
  Plus,
  Search,
  Activity,
  X,
  Trash2,
  AlertCircle,
  Shield,
  Clock,
  CheckCircle,
  XCircle,
  ExternalLink,
  ChevronRight,
  Key,
} from "lucide-react";
import { useDebounce } from "../hooks/useDebounce";
import { useScanWebSocket } from "../hooks/useScanWebSocket";
import { PageSkeleton } from "../components/PageSkeleton";
import { EmptyState } from "../components/EmptyState";
import { useToast } from "../components/Toast";

/**
 * Memoized ProjectRow to prevent re-rendering when the search term changes
 * but the project data remains identical.
 */
const ProjectRow = memo(({ project }: { project: Project }) => {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const deleteProjectMutation = useMutation({
    mutationFn: () => api.projects.delete(project.project_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setShowDeleteConfirm(false);
      addToast({
        type: "success",
        title: "Project Deleted",
        message: `Project "${project.name}" has been removed from the fleet.`,
      });
    },
    onError: (error) => {
      console.error("Failed to delete project:", error);
      addToast({
        type: "error",
        title: "Deletion Failed",
        message: `Failed to delete project "${project.name}".`,
      });
    },
  });

  const getStatusDisplay = (state: string | null) => {
    switch (state) {
      case "COMPLETED":
        return {
          color: "text-green-600 bg-green-50",
          icon: <CheckCircle className="w-4 h-4" />,
        };
      case "FAILED":
        return {
          color: "text-red-600 bg-red-50",
          icon: <AlertCircle className="w-4 h-4" />,
        };
      case "RUNNING":
      case "QUEUED":
      case "CREATED":
        return {
          color: "text-blue-600 bg-blue-50",
          icon: <Clock className="w-4 h-4 animate-pulse" />,
        };
      case "CANCELLED":
        return {
          color: "text-slate-600 bg-slate-50",
          icon: <XCircle className="w-4 h-4" />,
        };
      default:
        return {
          color: "text-slate-500 bg-slate-50",
          icon: <Activity className="w-4 h-4" />,
        };
    }
  };

  const status = getStatusDisplay(project.last_scan_state ?? null);

  return (
    <tr className="hover:bg-slate-50/50 transition-colors group">
      <td className="px-6 py-5">
        <div className="flex flex-col">
          <span className="font-bold text-slate-900 leading-tight mb-1">
            {project.name}
          </span>
          <span className="text-xs font-medium text-slate-400 font-mono tracking-tight">
            {project.project_id}
          </span>
        </div>
      </td>
      <td className="px-6 py-5">
        {project.last_scan_id ? (
          <Link
            to={`/scans/${project.last_scan_id}`}
            aria-label={`View latest scan results for ${project.name}. Current status: ${project.last_scan_state || "No Scans"}`}
            className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-all active:scale-95 hover:shadow-md ${status.color} ${
              project.last_scan_state === "RUNNING" ||
              project.last_scan_state === "QUEUED"
                ? "hover:bg-blue-100"
                : project.last_scan_state === "FAILED"
                  ? "hover:bg-red-100"
                  : "hover:bg-green-100"
            }`}
          >
            {status.icon}
            {project.last_scan_state || "No Scans"}
            <ChevronRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
          </Link>
        ) : (
          <div
            className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider ${status.color}`}
          >
            {status.icon}
            No Scans
          </div>
        )}
      </td>
      <td className="px-6 py-5 text-right">
        <div className="flex items-center justify-end gap-3">
          {!showDeleteConfirm ? (
            <>
              {project.last_scan_id && (
                <Link
                  to={`/scans/${project.last_scan_id}`}
                  className="inline-flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 rounded-xl text-xs font-bold transition-all active:scale-95 shadow-sm"
                  title="View latest scan"
                >
                  <ExternalLink className="w-4 h-4" />
                  Latest Scan
                </Link>
              )}
              <Link
                to={`/projects/${project.project_id}`}
                className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-xl text-sm font-bold transition-all active:scale-95 shadow-sm"
                title="Manage project configuration and scans"
                aria-label={`Manage project: ${project.name}`}
              >
                <Activity className="w-4 h-4" />
                Manage
              </Link>
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all active:scale-90"
                title="Delete project"
                aria-label={`Delete project ${project.name}`}
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </>
          ) : (
            <div className="flex items-center gap-2 animate-in slide-in-from-right-2 duration-200">
              <span className="text-xs font-bold text-red-600 mr-1 uppercase tracking-wider">
                Confirm Delete?
              </span>
              <button
                onClick={() => deleteProjectMutation.mutate()}
                disabled={deleteProjectMutation.isPending}
                className="px-3 py-1.5 bg-red-600 text-white rounded-lg text-xs font-bold hover:bg-red-700 disabled:opacity-50 shadow-sm"
              >
                Delete
              </button>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-3 py-1.5 bg-white border border-slate-200 text-slate-600 rounded-lg text-xs font-bold hover:bg-slate-50 shadow-sm"
              >
                No
              </button>
            </div>
          )}
        </div>
      </td>
    </tr>
  );
});

ProjectRow.displayName = "ProjectRow";

const ACTIVE_STATES = new Set(["CREATED", "QUEUED", "RUNNING"]);

const DashboardPage = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [showApikeyBanner, setShowApikeyBanner] = useState(false);
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  useEffect(() => {
    const apiKey =
      sessionStorage.getItem("API_KEY") || import.meta.env.VITE_API_KEY;
    if (!apiKey) {
      setShowApikeyBanner(true);
    }
  }, []);

  // WebSocket for real-time dashboard updates (Phase 3.1)
  const { connected: wsConnected } = useScanWebSocket(undefined, undefined, {
    onMessage: (message) => {
      console.log("Dashboard real-time update received:", message);
      // Performance Optimization (Bolt ⚡): Use surgical cache update instead of full invalidation
      // This prevents a redundant HTTP fetch and preserves object references for React.memo
      queryClient.setQueryData<Project[]>(["projects"], (oldProjects) => {
        if (!oldProjects) return oldProjects;
        return oldProjects.map((p) => {
          if (p.project_id === message.project_id) {
            // Only update if state or last_scan_id actually changed to minimize re-renders
            if (p.last_scan_state === message.data.state && p.last_scan_id === message.scan_id) {
              return p;
            }
            return {
              ...p,
              last_scan_state: message.data.state,
              last_scan_id: message.scan_id,
            };
          }
          return p;
        });
      });
    },
    onOpen: () => {
      console.log("Dashboard WebSocket connected");
    },
  });

  const { data: projects = [], isLoading: loading } = useQuery({
    queryKey: ["projects"],
    queryFn: api.projects.list,
    refetchInterval: wsConnected ? false : 10000,
  });

  // Performance: Debounce search input to avoid re-filtering and re-renders on every keystroke
  const debouncedSearchTerm = useDebounce(searchTerm, 300);

  // Performance: Memoize filtered projects to avoid re-calculating on every render.
  const hasActiveScan = useMemo(
    () => projects.some((p) => ACTIVE_STATES.has(p.last_scan_state ?? "")),
    [projects],
  );

  const filteredProjects = useMemo(() => {
    if (!debouncedSearchTerm) return projects;

    const lowerSearch = debouncedSearchTerm.toLowerCase();
    return projects.filter((project) =>
      project.name.toLowerCase().includes(lowerSearch),
    );
  }, [projects, debouncedSearchTerm]);

  if (loading) return <PageSkeleton type="dashboard" />;

  return (
    <div className="space-y-6 px-4 py-8 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h2 className="text-4xl font-black text-slate-900 tracking-tight leading-none mb-2">
            Project Pipeline
          </h2>
          <p className="text-slate-500 text-sm font-medium">
            Manage and monitor your security scan infrastructure
          </p>
        </div>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
          <div className="relative group min-w-[300px]">
            <Search
              className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-blue-500 transition-colors"
              aria-hidden="true"
            />
            <input
              type="text"
              placeholder="Search secure projects..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              aria-label="Search projects"
              className="w-full pl-11 pr-11 py-3 bg-white border border-slate-200 rounded-2xl text-sm font-bold focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 outline-none transition-all shadow-sm shadow-slate-100"
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => setSearchTerm("")}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition-colors"
                aria-label="Clear search"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          <button
            onClick={() => navigate("/projects/create")}
            className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-2xl text-sm font-black transition-all active:scale-95 shadow-xl shadow-blue-200"
          >
            <Plus className="w-5 h-5" />
            NEW PROJECT
          </button>
        </div>
      </div>

      {/* API Key Setup Banner */}
      {showApikeyBanner && (
        <div className="bg-amber-50 border-2 border-amber-200 rounded-[2rem] px-8 py-6 text-amber-900 shadow-xl shadow-amber-100 flex flex-col md:flex-row md:items-center justify-between gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
          <div className="flex items-start gap-5 flex-1">
            <div className="w-14 h-14 bg-amber-100 rounded-2xl flex items-center justify-center flex-shrink-0 border border-amber-200">
              <Key className="w-7 h-7 text-amber-600" />
            </div>
            <div className="space-y-2">
              <div className="font-black text-lg tracking-tight">
                API Key Not Configured
              </div>
              <div className="text-amber-700 text-xs font-medium leading-relaxed">
                To enable scan management features (reset, cancel), configure
                your API key in Settings. Without it, you can view scans but
                cannot control them.
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3 self-stretch md:self-auto">
            <button
              onClick={() => navigate("/settings")}
              className="px-6 py-3 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-black uppercase tracking-widest transition-all active:scale-95 shadow-lg shadow-amber-200 whitespace-nowrap"
            >
              Configure Now
            </button>
            <button
              onClick={() => setShowApikeyBanner(false)}
              className="px-4 py-3 text-amber-600 hover:bg-amber-100 rounded-xl transition-colors"
              aria-label="Dismiss banner"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {hasActiveScan && (
        <div className="bg-blue-600 rounded-[2rem] px-8 py-6 text-white shadow-2xl shadow-blue-100 flex flex-col md:flex-row md:items-center justify-between gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
          <div className="flex items-center gap-5">
            <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center animate-pulse border border-white/30">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <div>
              <div className="font-black text-lg tracking-tight">
                Security Scan Active
              </div>
              <div className="text-blue-100 text-xs font-bold uppercase tracking-widest opacity-80">
                System is processing security pipeline stages.
              </div>
            </div>
          </div>
          <div className="text-[10px] font-black uppercase tracking-[0.2em] bg-white/20 px-4 py-2 rounded-xl border border-white/30 backdrop-blur-sm self-start md:self-center">
            Real-time Monitoring
          </div>
        </div>
      )}

      {filteredProjects.length === 0 ? (
        <div className="py-12">
          {debouncedSearchTerm ? (
            <div className="bg-white border border-slate-200 rounded-[2.5rem] p-20 text-center shadow-sm">
              <div className="bg-slate-50 w-20 h-20 rounded-[2rem] flex items-center justify-center mx-auto mb-6 border border-dashed border-slate-200">
                <Search className="w-10 h-10 text-slate-300" />
              </div>
              <h3 className="text-2xl font-black text-slate-900 tracking-tight mb-2 uppercase">
                No matches found
              </h3>
              <p className="text-slate-500 text-sm font-medium mb-8">
                Try adjusting your search terms for "{debouncedSearchTerm}"
              </p>
              <button
                onClick={() => setSearchTerm("")}
                className="text-blue-600 font-black uppercase text-xs tracking-widest hover:text-blue-700 transition-colors"
              >
                Clear Search Results
              </button>
            </div>
          ) : (
            <EmptyState
              icon={Shield}
              title="No Projects Monitored"
              description="Start your security pipeline by adding your first git repository for continuous vulnerability scanning and automated reporting."
              actionLabel="CREATE FIRST PROJECT"
              onAction={() => navigate("/projects/create")}
            />
          )}
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-[2.5rem] shadow-xl shadow-slate-100/50 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead className="bg-slate-50/50 border-b border-slate-100">
                <tr>
                  <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                    Project Name & ID
                  </th>
                  <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
                    Pipeline Health
                  </th>
                  <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] text-right">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {filteredProjects.map((project) => (
                  <ProjectRow key={project.project_id} project={project} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
