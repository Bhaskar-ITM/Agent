import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import {
  ChevronLeft, Play, Settings2, Info, GitBranch, ShieldCheck,
  Globe, MapPin, X, Copy, Check, History, Pencil,
} from 'lucide-react';
import { ConfirmModal } from '../components/ConfirmModal';
import { useToast } from '../components/Toast';

const ProjectControlPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { success, error: toastError } = useToast();
  const [project, setProject] = useState<{
    project_id: string; name: string; git_url: string; branch: string;
    sonar_key: string; target_ip?: string; target_url?: string; last_scan_state?: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanLoading, setScanLoading] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [hasActiveScan, setHasActiveScan] = useState(false);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const handleCopy = (text: string, fieldId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldId);
    setTimeout(() => setCopiedField(null), 2000);
  };

  useEffect(() => {
    if (id) {
      api.projects.get(id).then(data => {
        if (data) {
          setProject(data);
          const ACTIVE = new Set(['CREATED', 'QUEUED', 'RUNNING']);
          setHasActiveScan(ACTIVE.has(data.last_scan_state ?? ''));
        }
        setLoading(false);
      });
    }
  }, [id]);

  const handleRunAutomated = async () => {
    if (!id) return;
    setScanLoading(true);
    setShowConfirm(false);
    try {
      const scan = await api.scans.trigger(id, 'automated');
      success('Scan started', 'Automated security scan is now running.');
      navigate(`/scans/${scan.scan_id}`);
    } catch (err: unknown) {
      const errorObj = err as { response?: { status?: number; data?: { detail?: string } } };
      if (errorObj?.response?.status === 409) {
        toastError('Scan already running', 'Please wait for the current scan to complete.');
      } else if (errorObj?.response?.status === 401) {
        toastError('Unauthorized', 'Verify your API key configuration.');
      } else {
        toastError('Failed to start scan', errorObj?.response?.data?.detail || 'An unexpected error occurred.');
      }
      setScanLoading(false);
    }
  };

  if (loading && !project) {
    return (
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="h-8 w-40 bg-slate-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-2 bg-white border border-slate-200 rounded-2xl p-8 space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-5 bg-slate-100 rounded animate-pulse" style={{ width: `${60 + i * 8}%` }} />
            ))}
          </div>
          <div className="space-y-4">
            <div className="h-48 bg-slate-200 rounded-2xl animate-pulse" />
            <div className="h-48 bg-slate-200 rounded-2xl animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-20 text-red-500">Project not found.</div>
    );
  }

  const DetailRow = ({
    icon: Icon, label, value, copyId,
  }: {
    icon: React.ElementType; label: string; value: string | undefined; copyId?: string;
  }) => (
    <div className="space-y-1 group">
      <div className="flex items-center gap-2 text-slate-400 text-xs font-semibold uppercase tracking-wider">
        <Icon className="w-3 h-3" />
        {label}
      </div>
      <div className="flex items-center gap-2">
        <span className="text-slate-700 font-medium text-sm break-all">
          {value || <span className="text-slate-400 font-normal italic">Not configured</span>}
        </span>
        {value && copyId && (
          <button
            type="button"
            onClick={() => handleCopy(value, copyId)}
            className="p-1 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity text-slate-400 hover:text-blue-600"
            aria-label={`Copy ${label}`}
          >
            {copiedField === copyId ? (
              <Check className="w-3 h-3 text-emerald-500" />
            ) : (
              <Copy className="w-3 h-3" />
            )}
          </button>
        )}
      </div>
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => navigate('/dashboard')}
          className="flex items-center gap-2 text-slate-500 hover:text-slate-800 transition-colors text-sm"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Dashboard
        </button>
        {/* Edit project shortcut */}
        <Link
          to={`/projects/${project.project_id}/edit`}
          className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-blue-600 px-3 py-1.5 rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition-all"
        >
          <Pencil className="w-3.5 h-3.5" />
          Edit Project
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Project Details */}
        <div className="md:col-span-2 space-y-6">
          <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm">
            <div className="flex items-start justify-between mb-6">
              <h2 className="text-2xl font-bold text-slate-900">{project.name}</h2>
              <Link
                to={`/projects/${project.project_id}/edit`}
                className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-blue-600 transition-colors mt-1"
              >
                <Pencil className="w-3.5 h-3.5" />
                Edit
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-6 gap-x-12">
              <DetailRow icon={Globe}      label="Repository URL"  value={project.git_url}    copyId="repo" />
              <DetailRow icon={GitBranch}  label="Branch"          value={project.branch} />
              <DetailRow icon={ShieldCheck} label="Sonar Key"       value={project.sonar_key}  copyId="sonar" />
              <DetailRow icon={MapPin}     label="Target IP"        value={project.target_ip} />
              <div className="sm:col-span-2">
                <DetailRow icon={Globe}    label="Target URL"       value={project.target_url} />
              </div>
            </div>
          </div>
        </div>

        {/* Scan Actions */}
        <div className="space-y-4">
          {/* Automated scan */}
          <div className="bg-blue-600 rounded-2xl p-6 text-white shadow-lg shadow-blue-200">
            <h3 className="text-lg font-bold mb-1.5">Automated Scan</h3>
            <p className="text-blue-100 text-sm mb-5 leading-relaxed">
              Let the system decide which security stages to run automatically.
            </p>
            <button
              onClick={() => setShowConfirm(true)}
              disabled={hasActiveScan || scanLoading}
              className="w-full bg-white text-blue-600 hover:bg-blue-50 py-2.5 rounded-xl font-bold flex items-center justify-center gap-2 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              <Play className="w-4 h-4 fill-current" />
              {hasActiveScan ? 'Scan in Progress…' : scanLoading ? 'Starting…' : 'Run Now'}
            </button>
          </div>

          {/* Manual scan */}
          <div className="bg-slate-900 rounded-2xl p-6 text-white shadow-lg shadow-slate-200">
            <h3 className="text-lg font-bold mb-1.5 text-slate-200">Manual Scan</h3>
            <p className="text-slate-400 text-sm mb-5 leading-relaxed">
              Select specific stages to execute from the full pipeline.
            </p>
            <Link
              to={`/projects/${project.project_id}/manual`}
              className="w-full bg-slate-800 text-white hover:bg-slate-700 py-2.5 rounded-xl font-bold flex items-center justify-center gap-2 transition-all active:scale-95 border border-slate-700 text-sm"
            >
              <Settings2 className="w-4 h-4" />
              Configure
            </Link>
          </div>

          {/* Edit project */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <h3 className="text-base font-bold mb-1 text-slate-900">Project Settings</h3>
            <p className="text-slate-500 text-sm mb-4">Update repository URL, credentials, or targets.</p>
            <Link
              to={`/projects/${project.project_id}/edit`}
              className="w-full bg-slate-100 text-slate-700 hover:bg-slate-200 py-2.5 rounded-xl font-bold flex items-center justify-center gap-2 transition-all border border-slate-200 text-sm"
            >
              <Pencil className="w-4 h-4" />
              Edit Project
            </Link>
          </div>

          {/* Scan history */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <h3 className="text-base font-bold mb-1 text-slate-900">Scan History</h3>
            <p className="text-slate-500 text-sm mb-4">View all previous scans and their results.</p>
            <Link
              to={`/projects/${project.project_id}/history`}
              className="w-full bg-slate-100 text-slate-700 hover:bg-slate-200 py-2.5 rounded-xl font-bold flex items-center justify-center gap-2 transition-all border border-slate-200 text-sm"
            >
              <History className="w-4 h-4" />
              View History
            </Link>
          </div>
        </div>
      </div>

      {/* Confirmation Modal — replaces native confirm() */}
      <ConfirmModal
        isOpen={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={handleRunAutomated}
        isLoading={scanLoading}
        variant="info"
        title="Start Automated Scan"
        description={
          <>
            This will trigger a full automated security scan for{' '}
            <span className="font-semibold text-slate-900">{project.name}</span>.
            The system will automatically select and run all relevant security stages.
          </>
        }
        confirmLabel="Confirm & Run"
        cancelLabel="Cancel"
      />
    </div>
  );
};

export default ProjectControlPage;
