import { useState, useEffect, memo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../services/api';
import type { Scan, Project, ScanStage } from '../types';
import {
  ChevronLeft,
  CheckCircle2,
  XCircle,
  Clock,
  RotateCw,
  ExternalLink,
  MinusCircle,
  Activity,
  History
} from 'lucide-react';

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'PASSED': return <CheckCircle2 className="w-5 h-5 text-green-500" />;
    case 'FAILED': return <XCircle className="w-5 h-5 text-red-500" />;
    case 'RUNNING': return <RotateCw className="w-5 h-5 text-blue-500 animate-spin" />;
    case 'SKIPPED': return <MinusCircle className="w-5 h-5 text-slate-300" />;
    default: return <Clock className="w-5 h-5 text-slate-300" />;
  }
};

const getStatusClass = (status: string) => {
  switch (status) {
    case 'PASSED': return 'bg-green-50 text-green-700 border-green-100';
    case 'FAILED': return 'bg-red-50 text-red-700 border-red-100';
    case 'RUNNING': return 'bg-blue-50 text-blue-700 border-blue-100';
    case 'SKIPPED': return 'bg-slate-50 text-slate-500 border-slate-100';
    default: return 'bg-slate-50 text-slate-400 border-slate-100';
  }
};

const StageRow = memo(({ stage, index }: { stage: ScanStage; index: number }) => (
  <div
    className={`flex items-center justify-between p-6 border-b border-slate-50 last:border-0 transition-colors ${
      stage.status === 'RUNNING' ? 'bg-blue-50/30' : ''
    }`}
  >
    <div className="flex items-center gap-6">
      <div className="w-8 h-8 flex items-center justify-center font-bold text-slate-300 text-lg">
        {String(index + 1).padStart(2, '0')}
      </div>
      <div>
        <div className="font-bold text-slate-800">{stage.name}</div>
        <div className="text-xs text-slate-400 uppercase font-semibold mt-0.5">
          {stage.status === 'SKIPPED' ? 'Not requested' : 'Security Check'}
        </div>
      </div>
    </div>

    <div className="flex items-center gap-8">
      <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-bold min-w-[120px] justify-center ${getStatusClass(stage.status)}`}>
        {getStatusIcon(stage.status)}
        {stage.status}
      </div>

      <div className="w-32 flex justify-end">
        {stage.reportUrl && stage.status === 'PASSED' && (
          <a
            href={stage.reportUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-blue-600 hover:text-blue-800 text-sm font-bold transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            Report
          </a>
        )}
      </div>
    </div>
  </div>
), (prev, next) => prev.stage.status === next.stage.status && prev.stage.reportUrl === next.stage.reportUrl);

const ScanStatusPage = () => {
  const { id } = useParams<{ id: string }>();
  const [scan, setScan] = useState<Scan | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);

  // Initial fetch: Load scan and project data once.
  useEffect(() => {
    let isMounted = true;
    const fetchInitialData = async () => {
      if (!id) return;
      const scanData = await api.scans.get(id);
      if (scanData && isMounted) {
        setScan(scanData);
        const projectData = await api.projects.get(scanData.projectId);
        if (projectData && isMounted) setProject(projectData);
      }
      if (isMounted) setLoading(false);
    };
    fetchInitialData();
    return () => { isMounted = false; };
  }, [id]);

  // Polling fetch: Only runs when the scan is in RUNNING status.
  useEffect(() => {
    if (!id || scan?.status !== 'RUNNING') return;

    const pollInterval = setInterval(async () => {
      const scanData = await api.scans.get(id);
      if (scanData) setScan(scanData);
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [id, scan?.status]);

  if (loading && !scan) return <div className="p-8">Loading scan results...</div>;
  if (!scan) return <div className="p-8 text-center text-red-500">Scan not found</div>;

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <Link
          to={`/projects/${scan.projectId}`}
          className="flex items-center gap-2 text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Project
        </Link>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-400 font-medium">SCAN ID: {scan.id}</span>
          <div className={`px-4 py-1 rounded-full text-sm font-bold border ${
            scan.status === 'COMPLETED' ? 'bg-green-100 text-green-700 border-green-200' :
            scan.status === 'FAILED' ? 'bg-red-100 text-red-700 border-red-200' :
            'bg-blue-100 text-blue-700 border-blue-200 animate-pulse'
          }`}>
            {scan.status}
          </div>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-8 border-b border-slate-100 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-2xl font-bold text-slate-900">{project?.name}</h2>
              <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs font-bold uppercase">
                {scan.mode} MODE
              </span>
            </div>
            <div className="flex items-center gap-4 text-slate-500 text-sm">
              <div className="flex items-center gap-1">
                <Activity className="w-4 h-4" />
                Started: {new Date(scan.createdAt).toLocaleString()}
              </div>
              <div className="flex items-center gap-1">
                <History className="w-4 h-4" />
                Type: {scan.mode === 'AUTOMATED' ? 'System Optimized' : 'User Defined'}
              </div>
            </div>
          </div>
        </div>

        <div className="p-0">
          <div className="grid grid-cols-1">
            {scan.stages.map((stage, index) => (
              <StageRow key={index} stage={stage} index={index} />
            ))}
          </div>
        </div>
      </div>

      {scan.status === 'COMPLETED' && (
        <div className="bg-green-600 rounded-2xl p-8 text-white flex items-center justify-between shadow-lg shadow-green-100">
          <div>
            <h3 className="text-xl font-bold mb-1">Scan Successfully Completed</h3>
            <p className="text-green-100">All requested security stages have been executed. Review individual reports above.</p>
          </div>
          <button
            onClick={() => window.print()}
            className="px-6 py-3 bg-white text-green-700 rounded-xl font-bold hover:bg-green-50 transition-colors shadow-sm"
          >
            Export Full Summary
          </button>
        </div>
      )}
    </div>
  );
};

export default ScanStatusPage;
