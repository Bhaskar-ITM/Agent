import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { FIXED_STAGES } from '../types';
import type { Project } from '../types';
import { ChevronLeft, Play, ShieldAlert, CheckCircle2, Globe, MapPin } from 'lucide-react';

const ManualScanPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [selectedStages, setSelectedStages] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      api.projects.get(id).then(data => {
        if (data) setProject(data);
        setLoading(false);
      });
    }
  }, [id]);

  const toggleStage = (stage: string) => {
    setSelectedStages(prev =>
      prev.includes(stage) ? prev.filter(s => s !== stage) : [...prev, stage]
    );
  };

  const handleRun = async () => {
    if (!id || selectedStages.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      // Mapping display names to backend IDs if needed, but here they match
      const scan = await api.scans.trigger(id, 'MANUAL', selectedStages, project?.target_url);
      navigate(`/scans/${scan.scan_id}`);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || err.response?.data?.error || "Failed to trigger scan");
      setLoading(false);
    }
  };

  const isNmapSelected = selectedStages.includes('Nmap Scan');
  const isZapSelected = selectedStages.includes('ZAP Scan');

  if (loading && !project) return <div className="p-8">Loading...</div>;
  if (!project) return <div className="p-8 text-center">Project not found</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <button
        onClick={() => navigate(`/projects/${id}`)}
        className="flex items-center gap-2 text-slate-500 hover:text-slate-800 transition-colors"
      >
        <ChevronLeft className="w-4 h-4" />
        Back to Project Control
      </button>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl flex items-center gap-3">
          <ShieldAlert className="w-5 h-5" />
          <span className="font-medium">{error}</span>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-8 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Manual Scan Selection</h2>
            <p className="text-slate-500 text-sm mt-1">Select the specific stages you want to execute for this scan.</p>
          </div>
          <div className="px-4 py-2 bg-blue-50 text-blue-700 rounded-lg text-sm font-bold border border-blue-100">
            {selectedStages.length} Stages Selected
          </div>
        </div>

        <div className="p-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            {FIXED_STAGES.map(stage => (
              <label
                key={stage}
                className={`flex items-center gap-4 p-4 rounded-xl border-2 cursor-pointer transition-all ${
                  selectedStages.includes(stage)
                    ? 'border-blue-500 bg-blue-50/50'
                    : 'border-slate-100 bg-white hover:border-slate-200'
                }`}
              >
                <input
                  type="checkbox"
                  className="hidden"
                  checked={selectedStages.includes(stage)}
                  onChange={() => toggleStage(stage)}
                />
                <div className={`w-6 h-6 rounded-md border-2 flex items-center justify-center transition-colors ${
                  selectedStages.includes(stage) ? 'bg-blue-600 border-blue-600' : 'border-slate-300 bg-white'
                }`}>
                  {selectedStages.includes(stage) && <CheckCircle2 className="w-4 h-4 text-white" />}
                </div>
                <span className={`font-semibold ${selectedStages.includes(stage) ? 'text-blue-900' : 'text-slate-700'}`}>
                  {stage}
                </span>
              </label>
            ))}
          </div>

          {/* Conditional Fields (Reflecting project config) */}
          {(isNmapSelected || isZapSelected) && (
            <div className="p-6 bg-slate-50 rounded-xl border border-slate-200 mb-8 space-y-6">
              <div className="flex items-center gap-2 text-slate-800 font-bold text-sm uppercase tracking-wider">
                <ShieldAlert className="w-4 h-4 text-amber-500" />
                Additional Configuration Status
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                {isNmapSelected && (
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-2">Target IP (for Nmap)</label>
                    <div className="relative">
                      <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <input
                        readOnly
                        value={project.target_ip || 'Not set in project'}
                        className="w-full pl-10 pr-4 py-2 bg-slate-100 border border-slate-200 rounded-lg text-slate-500 cursor-not-allowed italic"
                      />
                    </div>
                    {!project.target_ip && <p className="text-xs text-amber-600 mt-1 italic">Will fail in Manual mode</p>}
                  </div>
                )}
                {isZapSelected && (
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-2">Target URL (for ZAP)</label>
                    <div className="relative">
                      <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <input
                        readOnly
                        value={project.target_url || 'Not set in project'}
                        className="w-full pl-10 pr-4 py-2 bg-slate-100 border border-slate-200 rounded-lg text-slate-500 cursor-not-allowed italic"
                      />
                    </div>
                    {!project.target_url && <p className="text-xs text-amber-600 mt-1 italic">Will fail in Manual mode</p>}
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-6 border-t border-slate-100">
            <button
              onClick={() => navigate(`/projects/${id}`)}
              className="px-6 py-3 text-slate-600 font-semibold hover:bg-slate-50 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleRun}
              disabled={selectedStages.length === 0 || loading}
              className="px-10 py-3 bg-slate-900 text-white font-bold rounded-xl flex items-center gap-2 hover:bg-slate-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
            >
              <Play className="w-4 h-4 fill-current" />
              {loading ? 'Starting Scan...' : 'Start Manual Scan'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ManualScanPage;
