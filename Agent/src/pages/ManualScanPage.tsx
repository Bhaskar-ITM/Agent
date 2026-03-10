import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Play, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import { FIXED_STAGES, STAGE_DISPLAY_NAMES, type StageId } from '../types';

const ManualScanPage = () => {
  const { id: projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState<{ name: string; git_url: string; branch: string; target_ip?: string; target_url?: string } | null>(null);
  const [scanMode, setScanMode] = useState<'automated' | 'manual'>('manual');
  const [selectedStages, setSelectedStages] = useState<StageId[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isProjectLoading, setIsProjectLoading] = useState(true);

  useEffect(() => {
    const fetchProject = async () => {
      if (!projectId) return;
      setIsProjectLoading(true);
      try {
        const projectData = await api.projects.get(projectId);
        if (projectData) {
          setProject({
            name: projectData.name,
            git_url: projectData.git_url,
            branch: projectData.branch,
            target_ip: projectData.target_ip,
            target_url: projectData.target_url
          });
        }
      } catch (err) {
        console.error('Failed to fetch project:', err);
        setError('Failed to load project details');
      } finally {
        setIsProjectLoading(false);
      }
    };

    fetchProject();
  }, [projectId]);

  const handleStageToggle = (stage: StageId) => {
    setSelectedStages(prev =>
      prev.includes(stage)
        ? prev.filter(s => s !== stage)
        : [...prev, stage]
    );
  };

  const handleToggleAll = () => {
    if (selectedStages.length === FIXED_STAGES.length) {
      setSelectedStages([]);
    } else {
      setSelectedStages([...FIXED_STAGES]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (scanMode === 'manual' && selectedStages.length === 0) {
      setError('Please select at least one stage for manual scan');
      return;
    }

    setIsLoading(true);
    try {
      const scan = await api.scans.trigger(
        projectId!,
        scanMode,
        scanMode === 'manual' ? selectedStages : undefined
      );
      setSuccessMessage(`Scan started successfully! Scan ID: ${scan.scan_id}`);
      // Redirect to scan status page after 2 seconds
      setTimeout(() => {
        navigate(`/scans/${scan.scan_id}`);
      }, 2000);
    } catch (err: unknown) {
      console.error('Scan trigger failed', err);
      const errorMessage = err && typeof err === 'object' && 'response' in err
        ? (err.response as { data?: { detail?: string } })?.data?.detail
        : 'Scan trigger failed. Please try again.';
      setError(errorMessage || 'Scan trigger failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isProjectLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-sm p-8 flex items-center gap-4">
          <Loader2 className="animate-spin h-6 w-6 text-blue-600" />
          <span className="text-slate-700">Loading project details...</span>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-sm p-8 text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-slate-900 mb-2">Project Not Found</h2>
          <p className="text-slate-600 mb-6">The project you're looking for doesn't exist or has been removed.</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-6xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center gap-4 mb-6">
            <button
              onClick={() => navigate(`/projects/${projectId}`)}
              className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Project
            </button>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-slate-900">Manual Scan Configuration</h1>
              <p className="text-slate-600">Configure and trigger a manual security scan for {project.name}</p>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              {error}
            </div>
          )}

          {successMessage && (
            <div className="bg-green-50 text-green-600 p-4 rounded-lg mb-6 flex items-center gap-3">
              <CheckCircle className="w-5 h-5 flex-shrink-0" />
              {successMessage}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Project Information */}
            <div className="bg-slate-50 rounded-lg p-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-4">Project Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-slate-500">Project Name:</span>
                  <span className="ml-2 font-medium">{project.name}</span>
                </div>
                <div>
                  <span className="text-slate-500">Git URL:</span>
                  <span className="ml-2 font-medium">{project.git_url}</span>
                </div>
                <div>
                  <span className="text-slate-500">Branch:</span>
                  <span className="ml-2 font-medium">{project.branch}</span>
                </div>
              </div>
            </div>

            {/* Scan Mode Selection */}
            <div>
              <h2 className="text-lg font-semibold text-slate-900 mb-4">Scan Configuration</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-3">Scan Mode</label>
                  <div className="space-y-2">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="radio"
                        value="automated"
                        checked={scanMode === 'automated'}
                        onChange={(e) => setScanMode(e.target.value as 'automated' | 'manual')}
                        className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                      />
                      <div>
                        <div className="font-medium text-slate-900">Automated Scan</div>
                        <div className="text-sm text-slate-600">Run all security stages automatically</div>
                      </div>
                    </label>
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="radio"
                        value="manual"
                        checked={scanMode === 'manual'}
                        onChange={(e) => setScanMode(e.target.value as 'automated' | 'manual')}
                        className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                      />
                      <div>
                        <div className="font-medium text-slate-900">Manual Scan</div>
                        <div className="text-sm text-slate-600">Select specific stages to run</div>
                      </div>
                    </label>
                  </div>
                </div>

                {/* Stage Selection */}
                {scanMode === 'manual' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="block text-sm font-medium text-slate-700">Select Stages</label>
                      <span className="text-xs font-medium text-slate-500 px-2 py-1 bg-slate-100 rounded-full">
                        {selectedStages.length} Stages Selected
                      </span>
                    </div>
                    <div className="space-y-2 max-h-64 overflow-y-auto pr-2 border border-slate-100 rounded-lg p-2">
                      {FIXED_STAGES.map((stageId) => (
                        <label key={stageId} className="flex items-center gap-3 cursor-pointer hover:bg-slate-50 p-2 rounded transition-colors">
                          <input
                            type="checkbox"
                            checked={selectedStages.includes(stageId)}
                            onChange={() => handleStageToggle(stageId)}
                            className="w-4 h-4 text-blue-600 focus:ring-blue-500 rounded border-slate-300"
                          />
                          <span className="text-slate-900">{STAGE_DISPLAY_NAMES[stageId]}</span>
                        </label>
                      ))}
                    </div>
                    <div className="flex mt-1">
                      <button
                        type="button"
                        onClick={handleToggleAll}
                        aria-label={selectedStages.length === FIXED_STAGES.length ? "Deselect all stages" : "Select all stages"}
                        className="text-sm text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1 transition-colors"
                      >
                        {selectedStages.length === FIXED_STAGES.length ? "Deselect All" : "Select All"}
                      </button>
                    </div>

                    {/* Additional Configuration Status */}
                    {(selectedStages.includes('nmap_scan') || selectedStages.includes('zap_scan')) && (
                      <div className="mt-4 p-4 bg-blue-50 border border-blue-100 rounded-xl space-y-3">
                        <h3 className="text-sm font-bold text-blue-900 flex items-center gap-2">
                          <AlertCircle className="w-4 h-4" />
                          Additional Configuration Status
                        </h3>
                        {selectedStages.includes('nmap_scan') && (
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-blue-700 font-medium">Target IP (for Nmap)</span>
                            <span className={project.target_ip ? "text-green-600 font-bold" : "text-amber-600 font-bold"}>
                              {project.target_ip || 'Not Configured'}
                            </span>
                          </div>
                        )}
                        {selectedStages.includes('zap_scan') && (
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-blue-700 font-medium">Target URL (for ZAP)</span>
                            <span className={project.target_url ? "text-green-600 font-bold" : "text-amber-600 font-bold"}>
                              {project.target_url || 'Not Configured'}
                            </span>
                          </div>
                        )}
                        {(!project.target_ip && selectedStages.includes('nmap_scan')) || (!project.target_url && selectedStages.includes('zap_scan')) ? (
                          <p className="text-[10px] text-amber-700 italic mt-1">
                            Warning: Some selected stages require additional configuration to yield results.
                          </p>
                        ) : null}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex gap-4">
              <button
                type="submit"
                disabled={isLoading}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="animate-spin h-4 w-4" />
                    Starting Scan...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Start Scan
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={() => navigate(`/projects/${projectId}`)}
                className="border border-slate-300 text-slate-700 font-semibold px-6 py-3 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ManualScanPage;