import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import {
  ArrowLeft, Clock, CheckCircle, AlertCircle, XCircle,
  Loader2, RefreshCw, ClipboardList,
} from 'lucide-react';

interface ScanHistoryItem {
  scan_id: string;
  state: string;
  created_at: string;
  finished_at?: string;
  retry_count: number;
  error?: { message: string; error_type?: string };
}

const STATE_CONFIG: Record<string, { icon: React.ElementType; badge: string; row: string }> = {
  COMPLETED: { icon: CheckCircle, badge: 'bg-emerald-100 text-emerald-800 border-emerald-200',   row: 'hover:bg-emerald-50/50' },
  FAILED:    { icon: AlertCircle, badge: 'bg-red-100 text-red-800 border-red-200',               row: 'hover:bg-red-50/50' },
  CANCELLED: { icon: XCircle,     badge: 'bg-slate-100 text-slate-700 border-slate-200',          row: 'hover:bg-slate-50' },
  RUNNING:   { icon: Loader2,     badge: 'bg-blue-100 text-blue-800 border-blue-200',             row: 'hover:bg-blue-50/50' },
  QUEUED:    { icon: Clock,       badge: 'bg-amber-100 text-amber-800 border-amber-200',          row: 'hover:bg-amber-50/50' },
  CREATED:   { icon: Clock,       badge: 'bg-slate-100 text-slate-700 border-slate-200',          row: 'hover:bg-slate-50' },
};

function duration(created: string, finished?: string): string {
  if (!finished) return 'In progress';
  const ms = new Date(finished).getTime() - new Date(created).getTime();
  const secs = Math.floor(ms / 1000);
  if (secs < 60) return `${secs}s`;
  const mins = Math.floor(secs / 60);
  const rem = secs % 60;
  return rem > 0 ? `${mins}m ${rem}s` : `${mins}m`;
}

export default function ScanHistoryPage() {
  const { id: projectId } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: history = [], isLoading, refetch, isRefetching } = useQuery<ScanHistoryItem[]>({
    queryKey: ['scan-history', projectId],
    queryFn: () => api.projects.getScanHistory(projectId!),
    refetchInterval: 15_000,
  });

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(`/projects/${projectId}`)}
            className="flex items-center gap-2 text-slate-500 hover:text-slate-800 text-sm transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Project
          </button>
        </div>
        <button onClick={() => refetch()} disabled={isRefetching}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 px-3 py-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50">
          <RefreshCw className={`w-3.5 h-3.5 ${isRefetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div>
        <h1 className="text-2xl font-bold text-slate-900">Scan History</h1>
        <p className="text-slate-500 text-sm mt-1">
          Click any row to view full scan details and stage results.
        </p>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        {isLoading ? (
          <div className="divide-y divide-slate-100">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="px-6 py-4 flex items-center gap-6 animate-pulse">
                <div className="h-5 w-5 rounded-full bg-slate-200" />
                <div className="h-4 w-24 bg-slate-200 rounded" />
                <div className="h-4 w-36 bg-slate-100 rounded ml-auto" />
                <div className="h-4 w-16 bg-slate-100 rounded" />
                <div className="h-4 w-12 bg-slate-100 rounded" />
              </div>
            ))}
          </div>
        ) : history.length === 0 ? (
          <div className="flex flex-col items-center gap-4 py-16 px-6 text-center">
            <div className="w-14 h-14 bg-slate-100 rounded-2xl flex items-center justify-center">
              <ClipboardList className="w-7 h-7 text-slate-400" />
            </div>
            <div>
              <p className="text-slate-700 font-semibold mb-1">No scan history yet</p>
              <p className="text-slate-400 text-sm">Run your first scan to see results here.</p>
            </div>
            <Link to={`/projects/${projectId}`}
              className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
              Go to Project
            </Link>
          </div>
        ) : (
          <>
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Scan ID</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Started</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Duration</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Retries</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Error</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {history.map(scan => {
                  const cfg = STATE_CONFIG[scan.state] ?? STATE_CONFIG.CREATED;
                  const Icon = cfg.icon;
                  const isActive = scan.state === 'RUNNING' || scan.state === 'QUEUED';

                  return (
                    <tr
                      key={scan.scan_id}
                      onClick={() => navigate(`/scans/${scan.scan_id}`)}
                      className={`cursor-pointer transition-colors ${cfg.row}`}
                      title="View scan details"
                    >
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${cfg.badge}`}>
                          <Icon className={`w-3 h-3 ${isActive ? 'animate-spin' : ''}`} />
                          {scan.state}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-slate-600 font-mono">
                          {scan.scan_id.slice(0, 8)}…
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-600">
                        {new Date(scan.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-600">
                        {duration(scan.created_at, scan.finished_at)}
                      </td>
                      <td className="px-6 py-4">
                        {scan.retry_count > 0 ? (
                          <span className="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-medium">
                            {scan.retry_count}×
                          </span>
                        ) : (
                          <span className="text-xs text-slate-300">—</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {scan.error?.error_type ? (
                          <span className="text-xs text-red-600 font-medium truncate max-w-[140px] block">
                            {scan.error.error_type}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-300">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 text-xs text-slate-400">
              {history.length} scan{history.length !== 1 ? 's' : ''} total
            </div>
          </>
        )}
      </div>
    </div>
  );
}
