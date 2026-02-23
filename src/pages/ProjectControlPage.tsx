import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import type { Project } from '../types';
import { ChevronLeft, Play, Settings2, Info, GitBranch, ShieldCheck, Globe, MapPin, X, Copy, Check } from 'lucide-react';

const ProjectControlPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [showConfirm, setShowConfirm] = useState(false);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const handleCopy = (text: string, fieldId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldId);
    setTimeout(() => setCopiedField(null), 2000);
  };

  useEffect(() => {
    if (id) {
      api.projects.get(id).then(data => {
        if (data) setProject(data);
        setLoading(false);
      });
    }
  }, [id]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setShowConfirm(false);
    };
    if (showConfirm) {
      window.addEventListener('keydown', handleEscape);
    }
    return () => window.removeEventListener('keydown', handleEscape);
  }, [showConfirm]);

  const handleRunAutomated = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const scan = await api.scans.trigger(id, 'automated');
      navigate(`/scans/${scan.scan_id}`);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  if (loading && !project) return <div className="p-8">Loading project details...</div>;
  if (!project) return <div className="p-8 text-red-500 text-center">Project not found</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => navigate('/dashboard')}
          aria-label="Back to dashboard"
          className="flex items-center gap-2 text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" aria-hidden="true" />
          Back to Dashboard
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Project Details Card */}
        <div className="md:col-span-2 space-y-6">
          <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm">
            <h2 className="text-2xl font-bold text-slate-900 mb-6">{project.name}</h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-6 gap-x-12">
              <div className="space-y-1 group">
                <div className="flex items-center gap-2 text-slate-400 text-sm font-medium uppercase tracking-wider">
                  <Globe className="w-3 h-3" aria-hidden="true" />
                  Repository URL
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-slate-700 font-medium break-all">{project.git_url}</div>
                  <button
                    type="button"
                    onClick={() => handleCopy(project.git_url, 'repo')}
                    className="p-1 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity text-slate-400 hover:text-blue-600"
                    aria-label="Copy repository URL"
                  >
                    {copiedField === 'repo' ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
                  </button>
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-2 text-slate-400 text-sm font-medium uppercase tracking-wider">
                  <GitBranch className="w-3 h-3" aria-hidden="true" />
                  Branch
                </div>
                <div className="text-slate-700 font-medium">{project.branch}</div>
              </div>

              <div className="space-y-1 group">
                <div className="flex items-center gap-2 text-slate-400 text-sm font-medium uppercase tracking-wider">
                  <ShieldCheck className="w-3 h-3" aria-hidden="true" />
                  Sonar Key
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-slate-700 font-medium">{project.sonar_key}</div>
                  <button
                    type="button"
                    onClick={() => handleCopy(project.sonar_key, 'sonar')}
                    className="p-1 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity text-slate-400 hover:text-blue-600"
                    aria-label="Copy sonar project key"
                  >
                    {copiedField === 'sonar' ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
                  </button>
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-2 text-slate-400 text-sm font-medium uppercase tracking-wider">
                  <MapPin className="w-3 h-3" aria-hidden="true" />
                  Target IP
                </div>
                <div className="text-slate-700 font-medium">{project.target_ip || 'Not configured'}</div>
              </div>

              <div className="space-y-1 sm:col-span-2">
                <div className="flex items-center gap-2 text-slate-400 text-sm font-medium uppercase tracking-wider">
                  <Globe className="w-3 h-3" aria-hidden="true" />
                  Target URL
                </div>
                <div className="text-slate-700 font-medium">{project.target_url || 'Not configured'}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Scan Actions Card */}
        <div className="space-y-6">
          <div className="bg-blue-600 rounded-2xl p-6 text-white shadow-lg shadow-blue-200">
            <h3 className="text-lg font-bold mb-2">Automated Scan</h3>
            <p className="text-blue-100 text-sm mb-6">Let the system decide which security stages to run based on project configuration.</p>
            <button
              onClick={() => setShowConfirm(true)}
              className="w-full bg-white text-blue-600 hover:bg-blue-50 py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-all active:scale-95"
            >
              <Play className="w-4 h-4 fill-current" aria-hidden="true" />
              Run Now
            </button>
          </div>

          <div className="bg-slate-900 rounded-2xl p-6 text-white shadow-lg shadow-slate-200">
            <h3 className="text-lg font-bold mb-2 text-slate-200">Manual Scan</h3>
            <p className="text-slate-400 text-sm mb-6">Explicitly select which of the 11 security stages you want to execute.</p>
            <Link
              to={`/projects/${project.project_id}/manual`}
              className="w-full bg-slate-800 text-white hover:bg-slate-700 py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-all active:scale-95 border border-slate-700"
            >
              <Settings2 className="w-4 h-4" aria-hidden="true" />
              Configure
            </Link>
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirm && (
        <div
          className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
          onClick={() => setShowConfirm(false)}
        >
          <div
            className="bg-white rounded-2xl max-w-md w-full p-8 shadow-2xl animate-in zoom-in-95 duration-200 relative"
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-title"
            aria-describedby="modal-description"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setShowConfirm(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-2 rounded-lg hover:bg-slate-100 transition-colors"
              aria-label="Close confirmation"
            >
              <X className="w-5 h-5" aria-hidden="true" />
            </button>
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-6">
              <Info className="w-6 h-6 text-blue-600" aria-hidden="true" />
            </div>
            <h3 id="modal-title" className="text-xl font-bold text-slate-900 mb-2">Confirm Automated Scan</h3>
            <p id="modal-description" className="text-slate-500 mb-8 leading-relaxed">
              This will trigger a full automated security scan for <span className="font-semibold text-slate-900">{project.name}</span>. The system will automatically select and run relevant security stages.
            </p>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setShowConfirm(false)}
                className="flex-1 py-3 border border-slate-200 text-slate-600 rounded-xl hover:bg-slate-50 transition-colors font-semibold"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleRunAutomated}
                className="flex-1 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors font-semibold shadow-lg shadow-blue-200"
              >
                Confirm & Run
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectControlPage;
