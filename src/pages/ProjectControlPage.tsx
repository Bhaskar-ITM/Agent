import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { ChevronLeft, Play, Settings2, Info, GitBranch, ShieldCheck, Globe, MapPin, X, Copy, Check, History, Zap, ExternalLink, Cpu, HardDrive, Trash2, PencilLine, AlertCircle } from 'lucide-react';
import { ApiError } from '../utils/apiError';

const ProjectControlPage = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [project, setProject] = useState<{ 
    project_id: string; 
    name: string; 
    git_url: string; 
    branch: string; 
    sonar_key: string; 
    target_ip?: string; 
    target_url?: string; 
    last_scan_state?: string;
    last_scan_id?: string;
  } | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [showConfirm, setShowConfirm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [hasActiveScan, setHasActiveScan] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const handleCopy = (text: string, fieldId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldId);
    setTimeout(() => setCopiedField(null), 2000);
  };

  useEffect(() => {
    if (projectId) {
      api.projects.get(projectId).then(data => {
        if (data) {
          setProject(data);
          const ACTIVE = new Set(['CREATED', 'QUEUED', 'RUNNING']);
          setHasActiveScan(ACTIVE.has(data.last_scan_state ?? ''));
        }
        setLoading(false);
      }).catch(() => {
        setError('Failed to load project details');
        setLoading(false);
      });
    }
  }, [projectId]);

  const handleRunAutomated = async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      setError(null);
      const scan = await api.scans.trigger(projectId, 'automated');
      navigate(`/scans/${scan.scan_id}`);
    } catch (_: any) {
      const detail = 'Failed to trigger scan';
      setError(detail);
      setLoading(false);
      setShowConfirm(false);
    }
  };

  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (!projectId) return;
      await api.projects.delete(projectId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      navigate('/dashboard');
    },
    onError: (err) => {
      setError(ApiError.getErrorMessage(err, 'Failed to delete project'));
    }
  });

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
        <div className="flex flex-col items-center gap-1">
          <span className="text-slate-900 font-black tracking-tight text-lg uppercase">Synchronizing</span>
          <span className="text-slate-400 text-[10px] font-bold uppercase tracking-[0.2em] animate-pulse">Establishing secure link</span>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="max-w-xl mx-auto py-20 text-center space-y-6 bg-white border border-slate-200 rounded-[3rem] shadow-xl shadow-slate-100">
        <div className="w-20 h-20 bg-red-50 text-red-600 rounded-[2.5rem] flex items-center justify-center mx-auto shadow-inner">
          <AlertCircle className="w-10 h-10" />
        </div>
        <div>
          <h2 className="text-3xl font-black text-slate-900 tracking-tight uppercase mb-2 leading-none">Access Denied</h2>
          <p className="text-slate-500 font-medium leading-relaxed italic">The requested project blueprint is unavailable or has been archived.</p>
        </div>
        <button
          onClick={() => navigate('/dashboard')}
          className="px-10 py-4 bg-slate-900 text-white rounded-2xl font-black hover:bg-slate-800 transition-all active:scale-95 shadow-xl shadow-slate-200"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-16 pb-32 px-4">
      {/* Enhanced Header Area */}
      <header className="flex flex-col lg:flex-row lg:items-end justify-between gap-10 animate-in fade-in slide-in-from-top-4 duration-700">
        <div className="flex items-center gap-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="p-5 bg-white border border-slate-200 text-slate-400 hover:text-slate-900 hover:border-slate-300 rounded-[2rem] transition-all active:scale-90 shadow-sm group"
            aria-label="Return to fleet overview"
          >
            <ChevronLeft className="w-7 h-7 group-hover:-translate-x-1 transition-transform" />
          </button>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <span className="text-[10px] font-black text-blue-500 uppercase tracking-[0.3em]">Project Control Plane</span>
            </div>
            <h1 className="text-5xl font-black text-slate-900 tracking-tighter leading-none uppercase">{project.name}</h1>
            <div className="flex items-center gap-4 text-slate-400">
              <span className="text-xs font-bold uppercase tracking-widest font-mono bg-slate-100 px-3 py-1 rounded-lg">ID: {project.project_id.split('-')[0]}...</span>
              <div className="w-1.5 h-1.5 bg-slate-200 rounded-full"></div>
              <span className="text-xs font-bold uppercase tracking-widest italic">Stable Infrastructure</span>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="flex items-center gap-3 bg-white border border-slate-200 p-2 rounded-[2rem] shadow-xl shadow-slate-200/50">
            <div className={`px-6 py-3 rounded-[1.5rem] text-[10px] font-black uppercase tracking-widest flex items-center gap-3 border ${
              project.last_scan_state === 'COMPLETED' ? 'bg-green-50 text-green-600 border-green-100' :
              project.last_scan_state === 'FAILED' ? 'bg-red-50 text-red-600 border-red-100' :
              hasActiveScan ? 'bg-blue-50 text-blue-600 border-blue-100' : 'bg-slate-50 text-slate-400 border-slate-100'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                project.last_scan_state === 'COMPLETED' ? 'bg-green-500' :
                project.last_scan_state === 'FAILED' ? 'bg-red-500' :
                hasActiveScan ? 'bg-blue-500 animate-pulse' : 'bg-slate-300'
              }`}></div>
              Last State: {project.last_scan_state || 'Offline'}
            </div>
            {project.last_scan_id && (
              <Link 
                to={`/scans/${project.last_scan_id}`}
                className="p-3 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-2xl transition-all group"
                title="Review latest execution"
                aria-label="View latest scan results"
              >
                <ExternalLink className="w-5 h-5 group-hover:scale-110 transition-transform" />
              </Link>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Link
              to={`/projects/${project.project_id}/edit`}
              className="px-4 py-2 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center gap-2"
            >
              <PencilLine className="w-4 h-4" />
              Edit
            </Link>
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="px-4 py-2 bg-white border border-red-200 text-red-600 hover:bg-red-50 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              Delete
            </button>
          </div>
        </div>
      </header>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-6 rounded-[2.5rem] flex items-start gap-5 animate-shake shadow-2xl shadow-red-100">
          <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg border border-red-100">
            <AlertCircle className="w-6 h-6 text-red-600" />
          </div>
          <div>
            <div className="font-black uppercase tracking-widest text-[10px] mb-1.5 opacity-80">Security Link Interrupted</div>
            <div className="text-sm font-bold leading-relaxed">{error}</div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-16">
        {/* Main Configuration Content */}
        <div className="lg:col-span-8 space-y-16">
          <section className="bg-white border border-slate-200 rounded-[3rem] shadow-2xl shadow-slate-200/40 overflow-hidden group">
            <div className="px-12 py-10 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <h3 className="font-black text-slate-900 tracking-tight uppercase text-xs flex items-center gap-4">
                <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-200">
                  <ShieldCheck className="w-4 h-4 text-white" />
                </div>
                Project Blueprint Overview
              </h3>
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest font-mono">Verified Configuration</span>
            </div>
            
            <div className="p-12 grid grid-cols-1 md:grid-cols-2 gap-16">
              <div className="space-y-4">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-3">
                  <Globe className="w-3.5 h-3.5" />
                  Remote Perimeter
                </label>
                <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-100 group/item hover:border-blue-200 transition-colors">
                  <div className="text-sm font-bold text-slate-700 truncate mr-4">{project.git_url}</div>
                  <button 
                    onClick={() => handleCopy(project.git_url, 'git')} 
                    className="p-2 text-slate-300 hover:text-blue-600 transition-all active:scale-90"
                    aria-label="Copy repository URL"
                  >
                    {copiedField === 'git' ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="space-y-4">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-3">
                  <GitBranch className="w-3.5 h-3.5" />
                  Active Branch Delta
                </label>
                <div className="p-4 bg-slate-900 rounded-2xl border border-slate-800 shadow-xl">
                  <span className="text-sm font-black text-blue-400 uppercase tracking-widest">{project.branch}</span>
                </div>
              </div>

              <div className="space-y-4">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-3">
                  <Cpu className="w-3.5 h-3.5" />
                  SonarQube Reference
                </label>
                <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-100 group/item hover:border-blue-200 transition-colors">
                  <div className="text-sm font-bold text-slate-700 font-mono">{project.sonar_key}</div>
                  <button 
                    onClick={() => handleCopy(project.sonar_key, 'sonar')} 
                    className="p-2 text-slate-300 hover:text-blue-600 transition-all active:scale-90"
                    aria-label="Copy sonar project key"
                  >
                    {copiedField === 'sonar' ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="space-y-4">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-3">
                  <MapPin className="w-3.5 h-3.5" />
                  Network Infrastructure
                </label>
                <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 flex items-center justify-between italic">
                  <span className="text-sm font-bold text-slate-500">{project.target_ip || 'DE-CONFIGURED'}</span>
                  {!project.target_ip && <Info className="w-4 h-4 text-slate-300" />}
                </div>
              </div>

              <div className="space-y-4 md:col-span-2">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-3">
                  <HardDrive className="w-3.5 h-3.5" />
                  Staging/Production Endpoint
                </label>
                <div className="p-5 bg-blue-50/30 rounded-2xl border border-blue-100/50 text-sm font-bold text-slate-600 break-all leading-relaxed">
                  {project.target_url || 'Endpoint telemetry unavailable for this blueprint.'}
                </div>
              </div>
            </div>
          </section>

          {/* Historical Intelligence Section */}
          <section className="bg-slate-900 rounded-[3rem] p-12 text-white shadow-2xl shadow-blue-900/20 flex flex-col md:flex-row items-center gap-12 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-96 h-96 bg-blue-600/10 blur-[100px] rounded-full translate-x-32 -translate-y-32 group-hover:bg-blue-600/20 transition-all duration-1000"></div>
            <div className="w-28 h-28 bg-white/5 rounded-[2.5rem] flex items-center justify-center flex-shrink-0 border border-white/10 shadow-2xl group-hover:scale-110 transition-transform duration-500">
              <History className="w-12 h-12 text-blue-400" />
            </div>
            <div className="flex flex-col md:flex-row items-center gap-10 flex-1 relative z-10">
              <div className="flex-1 text-center md:text-left space-y-3">
                <h3 className="text-3xl font-black tracking-tight uppercase">Intelligence Archive</h3>
                <p className="text-slate-400 font-medium leading-relaxed">Review historical scan data, temporal trends, and compliance reports stored in our secure engine.</p>
              </div>
              <Link 
                to={`/projects/${project.project_id}/history`}
                className="px-10 py-5 bg-white text-slate-900 rounded-2xl font-black uppercase tracking-widest text-[10px] hover:bg-blue-50 transition-all active:scale-95 shadow-2xl shadow-black/40 flex items-center gap-3"
              >
                Access Archive
                <ChevronLeft className="w-4 h-4 rotate-180" />
              </Link>
            </div>
          </section>
        </div>

        {/* Tactical Engagement Area */}
        <aside className="lg:col-span-4 space-y-10">
          <div className="bg-blue-600 rounded-[3rem] p-10 text-white shadow-2xl shadow-blue-200 relative overflow-hidden group">
            <div className="absolute -right-10 -top-10 w-48 h-48 bg-white/10 rounded-full blur-[60px] group-hover:bg-white/20 transition-all duration-1000"></div>
            <div className="relative z-10 space-y-8">
              <div>
                <h3 className="text-2xl font-black mb-2 flex items-center gap-4 uppercase tracking-tighter">
                  <Zap className="w-6 h-6 fill-current" />
                  Tactical Scan
                </h3>
                <p className="text-blue-100 text-sm font-medium leading-relaxed opacity-90">Execute the full automated security pipeline across all integrated toolsets immediately.</p>
              </div>
              <button
                onClick={() => setShowConfirm(true)}
                disabled={hasActiveScan}
                className="w-full bg-white text-blue-600 hover:bg-blue-50 py-5 rounded-[1.5rem] font-black uppercase tracking-[0.2em] text-[10px] transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed shadow-2xl shadow-blue-900/30 flex items-center justify-center gap-3"
              >
                <Play className="w-4 h-4 fill-current" />
                Initialize Engine
              </button>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-[3rem] p-10 shadow-2xl shadow-slate-200/50 space-y-8 group hover:border-slate-300 transition-colors">
            <div>
              <h3 className="text-2xl font-black mb-2 text-slate-900 flex items-center gap-4 uppercase tracking-tighter">
                <Settings2 className="w-6 h-6 text-slate-400 group-hover:text-blue-600 transition-colors" />
                Modular Config
              </h3>
              <p className="text-slate-500 text-sm font-medium leading-relaxed">Granular control over security stages. Best for troubleshooting specific toolsets.</p>
            </div>
            <Link
              to={`/projects/${project.project_id}/manual`}
              className="w-full bg-slate-50 text-slate-900 hover:bg-slate-100 py-5 rounded-[1.5rem] font-black uppercase tracking-[0.2em] text-[10px] flex items-center justify-center gap-3 transition-all active:scale-[0.98] border border-slate-200 shadow-sm"
            >
              Configure Modular
            </Link>
          </div>

          <div className="p-8 bg-slate-50/50 rounded-[2.5rem] border border-slate-200 border-dashed relative">
            <div className="flex items-start gap-5">
              <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm border border-slate-100">
                <Info className="w-5 h-5 text-slate-400" />
              </div>
              <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest leading-loose">
                Pipeline lock: Only one tactical scan can be active per project. Modular scans are prioritized based on global engine capacity.
              </p>
            </div>
          </div>
        </aside>
      </div>

      {/* Enhanced Authorization Modal */}
      {showConfirm && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6" role="dialog" aria-modal="true">
          <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-md animate-in fade-in duration-500" onClick={() => setShowConfirm(false)}></div>
          <div className="bg-white rounded-[3.5rem] max-w-xl w-full p-12 shadow-2xl relative z-10 animate-in zoom-in-95 slide-in-from-bottom-10 duration-500 flex flex-col items-center text-center">
            <button 
              onClick={() => setShowConfirm(false)} 
              className="absolute top-10 right-10 p-4 text-slate-400 hover:text-slate-900 hover:bg-slate-100 rounded-2xl transition-all active:scale-90"
              aria-label="Close authorization prompt"
            >
              <X className="w-7 h-7" />
            </button>
            
            <div className="w-24 h-24 bg-blue-50 text-blue-600 rounded-[2.5rem] flex items-center justify-center mb-10 shadow-inner relative ring-8 ring-blue-50/50">
              <div className="absolute inset-0 bg-blue-100 rounded-[2.5rem] animate-ping opacity-20"></div>
              <Zap className="w-12 h-12 fill-current relative z-10" />
            </div>
            
            <h2 className="text-4xl font-black text-slate-900 tracking-tighter leading-none mb-6 uppercase">Authorize<br/>Tactical Scan?</h2>
            <p className="text-slate-500 font-medium leading-relaxed mb-12 italic px-4">
              You are about to trigger a comprehensive security assessment. This will consume pipeline resources and generate fresh telemetry for this perimeter.
            </p>
            
            <div className="flex flex-col w-full gap-4">
              <button
                onClick={handleRunAutomated}
                className="w-full btn-primary h-20 uppercase tracking-[0.2em] text-xs flex items-center justify-center gap-4"
              >
                <Play className="w-5 h-5 fill-current" />
                Initialize Scan Cluster
              </button>
              <button
                onClick={() => setShowConfirm(false)}
                className="w-full btn-secondary h-16 uppercase tracking-[0.2em] text-[10px]"
              >
                Abort Operation
              </button>
            </div>
          </div>
        </div>
      )}

      {showDeleteConfirm && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6" role="dialog" aria-modal="true">
          <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-md animate-in fade-in duration-500" onClick={() => setShowDeleteConfirm(false)}></div>
          <div className="bg-white rounded-[3.5rem] max-w-xl w-full p-12 shadow-2xl relative z-10 animate-in zoom-in-95 slide-in-from-bottom-10 duration-500 flex flex-col items-center text-center">
            <button 
              onClick={() => setShowDeleteConfirm(false)} 
              className="absolute top-10 right-10 p-4 text-slate-400 hover:text-slate-900 hover:bg-slate-100 rounded-2xl transition-all active:scale-90"
              aria-label="Close delete prompt"
            >
              <X className="w-7 h-7" />
            </button>
            
            <div className="w-24 h-24 bg-red-50 text-red-600 rounded-[2.5rem] flex items-center justify-center mb-10 shadow-inner relative ring-8 ring-red-50/50">
              <div className="absolute inset-0 bg-red-100 rounded-[2.5rem] animate-ping opacity-20"></div>
              <Trash2 className="w-12 h-12 relative z-10" />
            </div>
            
            <h2 className="text-4xl font-black text-slate-900 tracking-tighter leading-none mb-6 uppercase">Delete<br/>Project?</h2>
            <p className="text-slate-500 font-medium leading-relaxed mb-12 italic px-4">
              This will permanently remove the project, its scans, and stored artifacts. This action cannot be undone.
            </p>
            
            <div className="flex flex-col w-full gap-4">
              <button
                onClick={() => deleteMutation.mutate()}
                disabled={deleteMutation.isPending}
                className="w-full bg-red-600 hover:bg-red-700 text-white h-20 rounded-[2rem] uppercase tracking-[0.2em] text-xs flex items-center justify-center gap-4 disabled:opacity-50"
              >
                <Trash2 className="w-5 h-5" />
                Confirm Delete
              </button>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="w-full btn-secondary h-16 uppercase tracking-[0.2em] text-[10px]"
              >
                Abort Operation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectControlPage;
