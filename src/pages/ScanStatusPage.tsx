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
  AlertTriangle
} from 'lucide-react';

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'PASS': return <CheckCircle2 className="w-5 h-5 text-green-500" />;
    case 'FAIL': return <XCircle className="w-5 h-5 text-red-500" />;
    case 'WARN': return <AlertTriangle className="w-5 h-5 text-amber-500" />;
    case 'RUNNING': return <RotateCw className="w-5 h-5 text-blue-500 animate-spin" />;
    case 'SKIPPED': return <MinusCircle className="w-5 h-5 text-slate-300" />;
    default: return <Clock className="w-5 h-5 text-slate-300" />;
  }
};

const getStatusClass = (status: string) => {
  switch (status) {
    case 'PASS': return 'bg-green-50 text-green-700 border-green-100';
    case 'FAIL': return 'bg-red-50 text-red-700 border-red-100';
    case 'WARN': return 'bg-amber-50 text-amber-700 border-amber-100';
    case 'RUNNING': return 'bg-blue-50 text-blue-700 border-blue-100';
    case 'SKIPPED': return 'bg-slate-50 text-slate-500 border-slate-100';
    default: return 'bg-slate-50 text-slate-400 border-slate-100';
  }
};

/**
 * Memoized StageRow to prevent re-rendering of all stages when only one status changes.
 */
const StageRow = memo(({ item, index }: { item: ScanStage; index: number }) => (
  <div
    className={`flex items-center justify-between p-6 border-b border-slate-50 last:border-0 transition-colors ${
      item.status === 'RUNNING' ? 'bg-blue-50/30' : ''
    }`}
  >
    <div className="flex items-center gap-6">
      <div className="w-8 h-8 flex items-center justify-center font-bold text-slate-300 text-lg">
        {String(index + 1).padStart(2, '0')}
      </div>
      <div>
        <div className="font-bold text-slate-800">{item.stage}</div>
        <div className="text-xs text-slate-400 font-semibold mt-0.5 max-w-md">
          {item.summary || 'Security scanning stage'}
        </div>
      </div>
    </div>

    <div className="flex items-center gap-8">
      <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-bold min-w-[120px] justify-center ${getStatusClass(item.status)}`}>
        {getStatusIcon(item.status)}
        {item.status}
      </div>

      <div className="w-32 flex justify-end">
        {item.artifact_url && item.status !== 'SKIPPED' && (
          <a
            href={item.artifact_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-blue-600 hover:text-blue-800 text-sm font-bold transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            View Report
          </a>
        )}
      </div>
    </div>
  </div>
));

StageRow.displayName = 'StageRow';

const ScanStatusPage = () => {
  const { id } = useParams<{ id: string }>();
  const [scan, setScan] = useState<Scan | null>(null);
  const [results, setResults] = useState<ScanStage[]>([]);
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      if (!id || !isMounted) return;
      try {
        // Performance: Parallelize API calls to reduce network waterfall latency
        const [scanData, stageResults] = await Promise.all([
          api.scans.get(id),
          api.scans.getResults(id)
        ]);

        if (isMounted) {
          if (scanData) {
            // Performance: Only update scan state if metadata changed to prevent redundant re-renders
            setScan(prev => {
              if (prev && prev.state === scanData.state && prev.started_at === scanData.started_at) {
                return prev;
              }
              return scanData;
            });

            // Optimization: Stop polling if scan has reached a terminal state
            if (['COMPLETED', 'FAILED', 'CANCELLED'].includes(scanData.state)) {
              clearInterval(intervalId);
            }
          }

          if (stageResults) {
            setResults(prevResults => {
              // Performance: Fine-grained reconciliation to preserve stable object references.
              // This maximizes React.memo efficiency for StageRow components.
              let hasChanged = false;
              const nextResults = stageResults.map((newItem, idx) => {
                const prevItem = prevResults[idx];
                if (
                  prevItem &&
                  prevItem.stage === newItem.stage &&
                  prevItem.status === newItem.status &&
                  prevItem.summary === newItem.summary &&
                  prevItem.artifact_url === newItem.artifact_url
                ) {
                  return prevItem; // Keep stable reference
                }
                hasChanged = true;
                return newItem;
              });

              if (!hasChanged && prevResults.length === stageResults.length) {
                return prevResults;
              }
              return nextResults;
            });
          }
        }
      } catch (err) {
        console.error('Failed to fetch scan data:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    const intervalId = setInterval(fetchData, 3000);
    fetchData();
    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, [id]); // Removed 'project' from dependencies to fix the redundant fetch loop

  // Fetch project once scan is loaded
  useEffect(() => {
    if (scan?.project_id && !project) {
      api.projects.get(scan.project_id).then(data => {
        if (data) setProject(data);
      });
    }
  }, [scan?.project_id, project]);

  if (loading && !scan) return <div className="p-8">Loading scan status...</div>;
  if (!scan) return <div className="p-8 text-center text-red-500">Scan not found</div>;

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <Link
          to={`/projects/${scan.project_id}`}
          className="flex items-center gap-2 text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Project
        </Link>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-400 font-medium uppercase tracking-widest">SCAN {scan.scan_id.split('-')[0]}</span>
          <div className={`px-4 py-1 rounded-full text-sm font-bold border ${
            scan.state === 'COMPLETED' ? 'bg-green-100 text-green-700 border-green-200' :
            scan.state === 'FAILED' ? 'bg-red-100 text-red-700 border-red-200' :
            'bg-blue-100 text-blue-700 border-blue-200'
          }`}>
            {scan.state}
          </div>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-8 border-b border-slate-100 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-2xl font-bold text-slate-900">{project?.name || 'Loading project...'}</h2>
            </div>
            <div className="flex items-center gap-4 text-slate-500 text-sm">
              <div className="flex items-center gap-1">
                <Activity className="w-4 h-4" />
                Started: {scan.started_at ? new Date(scan.started_at).toLocaleString() : 'Just now'}
              </div>
            </div>
          </div>
        </div>

        <div className="p-0">
          <div className="grid grid-cols-1">
            {results.length === 0 ? (
              <div className="p-12 text-center text-slate-400 italic">
                Awaiting execution results from orchestration layer...
              </div>
            ) : (
              results.map((item, index) => (
                <StageRow key={`${item.stage}-${index}`} item={item} index={index} />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScanStatusPage;
