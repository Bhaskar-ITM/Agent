import { useState, useCallback, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft, RefreshCw, AlertCircle, CheckCircle, Clock,
  ExternalLink, XCircle, Loader2, Wifi, WifiOff,
} from 'lucide-react';
import { api } from '../services/api';
import { ApiError } from '../utils/apiError';
import type { ScanStage } from '../types';
import { useScanReset, useScanCancel } from '../hooks/useScanReset';
import { useScanWebSocket } from '../hooks/useScanWebSocket';
import { ScanErrorModal } from '../components/ScanErrorModal';
import { ConfirmModal } from '../components/ConfirmModal';
import { useToast } from '../components/Toast';
import { notificationService } from '../services/notifications';

// ─── helpers ────────────────────────────────────────────────────────────────

function getStatusColor(status: string) {
  const s = status.toLowerCase();
  if (s.includes('running') || s.includes('in progress')) return 'text-blue-600 bg-blue-50 border-blue-200';
  if (s.includes('pass') || s.includes('completed')) return 'text-emerald-600 bg-emerald-50 border-emerald-200';
  if (s.includes('fail') || s.includes('error')) return 'text-red-600 bg-red-50 border-red-200';
  if (s.includes('skip')) return 'text-amber-600 bg-amber-50 border-amber-200';
  return 'text-slate-500 bg-slate-50 border-slate-200';
}

function getStatusIcon(status: string) {
  const s = status.toLowerCase();
  if (s.includes('running') || s.includes('in progress')) return <Loader2 className="w-4 h-4 animate-spin" />;
  if (s.includes('pass') || s.includes('completed')) return <CheckCircle className="w-4 h-4" />;
  if (s.includes('fail') || s.includes('error')) return <AlertCircle className="w-4 h-4" />;
  return <Clock className="w-4 h-4" />;
}

function ElapsedTime({ startedAt }: { startedAt?: string }) {
  const [elapsed, setElapsed] = useState('');
  useEffect(() => {
    if (!startedAt) return;
    const tick = () => {
      const secs = Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000);
      const m = Math.floor(secs / 60);
      const s = secs % 60;
      setElapsed(m > 0 ? `${m}m ${s}s` : `${s}s`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [startedAt]);
  return elapsed ? <span className="text-slate-500 text-sm">Running for {elapsed}</span> : null;
}

// Empty state variants for different scan states
function StagesEmptyState({ scanState }: { scanState: string }) {
  if (scanState === 'RUNNING' || scanState === 'QUEUED') {
    return (
      <div className="text-center py-12 space-y-3">
        <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center mx-auto">
          <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
        </div>
        <p className="text-slate-700 font-medium">Stages updating…</p>
        <p className="text-slate-400 text-sm">Results will appear here as each stage completes.</p>
      </div>
    );
  }
  if (scanState === 'COMPLETED') {
    return (
      <div className="text-center py-12 space-y-3">
        <div className="w-12 h-12 bg-amber-50 rounded-full flex items-center justify-center mx-auto">
          <AlertCircle className="w-6 h-6 text-amber-500" />
        </div>
        <p className="text-slate-700 font-medium">Scan completed — no stage data returned</p>
        <p className="text-slate-400 text-sm">The Jenkins callback may not have included stage results.</p>
      </div>
    );
  }
  if (scanState === 'FAILED') {
    return (
      <div className="text-center py-12 space-y-3">
        <div className="w-12 h-12 bg-red-50 rounded-full flex items-center justify-center mx-auto">
          <XCircle className="w-6 h-6 text-red-500" />
        </div>
        <p className="text-slate-700 font-medium">Scan failed before any stages ran</p>
        <p className="text-slate-400 text-sm">Check the failure details below for more information.</p>
      </div>
    );
  }
  return (
    <div className="text-center py-12">
      <p className="text-slate-400 text-sm">No stage data available yet.</p>
    </div>
  );
}

// ─── main component ──────────────────────────────────────────────────────────

const ScanStatusPage = () => {
  const { id: scanId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [showErrorModal, setShowErrorModal] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);

  const notificationSentRef = useRef(false);
  const prevStateRef = useRef<string | null>(null);

  const resetMutation = useScanReset();
  const cancelMutation = useScanCancel();

  const fetchScanData = useCallback(async () => {
    if (!scanId) return null;
    const scanData = await api.scans.get(scanId);
    if (!scanData) return null;
    let results: ScanStage[] = scanData.results ?? [];
    if (!results.length) {
      try { results = await api.scans.getResults(scanId); } catch { /* not ready yet */ }
    }
    return { scan: scanData, stages: results };
  }, [scanId]);

  const { data, isLoading, isRefetching, refetch, error } = useQuery({
    queryKey: ['scan', scanId],
    queryFn: fetchScanData,
    refetchInterval: query => {
      const state = query.state.data?.scan?.state;
      return state === 'COMPLETED' || state === 'FAILED' || state === 'CANCELLED' ? false : 2000;
    },
    retry: 3,
    retryDelay: 1000,
  });

  const scan = data?.scan ?? null;
  const stages = data?.stages ?? [];

  // WebSocket for real-time updates
  const { connected: wsConnected } = useScanWebSocket(scanId, undefined, {
    onMessage: () => { queryClient.invalidateQueries({ queryKey: ['scan', scanId] }); },
  });

  // Notification — send once when scan transitions to terminal state
  useEffect(() => {
    if (!scan) return;
    const state = scan.state;
    if (state !== prevStateRef.current) {
      prevStateRef.current = state;
      if ((state === 'COMPLETED' || state === 'FAILED') && !notificationSentRef.current) {
        notificationSentRef.current = true;
        if (notificationService.isSupported() && notificationService.hasPermission()) {
          notificationService.showScanComplete(scan.scan_id, state);
        }
      }
    }
  }, [scan]);

  // Request notification permission only when scan enters RUNNING state
  useEffect(() => {
    if (scan?.state === 'RUNNING' && notificationService.isSupported() && !notificationService.hasPermission()) {
      notificationService.requestPermission();
    }
  }, [scan?.state]);

  const handleReset = async () => {
    if (!scan) return;
    setShowResetConfirm(false);
    resetMutation.mutate(scan.scan_id, {
      onSuccess: () => {
        success('Scan reset', 'You can now trigger a new scan.');
        refetch();
      },
      onError: (err: unknown) => {
        const e = err as { message?: string };
        toastError('Reset failed', e.message || 'Unable to reset the scan.');
      },
    });
  };

  const handleCancel = async () => {
    if (!scan) return;
    setShowCancelConfirm(false);
    cancelMutation.mutate(scan.scan_id, {
      onSuccess: () => {
        success('Scan cancelled', 'The scan has been stopped.');
        refetch();
      },
      onError: (err: unknown) => {
        const e = err as { message?: string };
        toastError('Cancel failed', e.message || 'Unable to cancel the scan.');
      },
    });
  };

  // ── loading skeleton ─────────────────────────────────────────────────────
  if (isLoading && !scan) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-6 animate-pulse">
          <div className="h-7 w-48 bg-slate-200 rounded" />
          <div className="grid grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => <div key={i} className="h-20 bg-slate-100 rounded-lg" />)}
          </div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => <div key={i} className="h-16 bg-slate-100 rounded-lg" />)}
          </div>
        </div>
      </div>
    );
  }

  if (!scan) {
    return (
      <div className="max-w-6xl mx-auto p-6 flex items-center justify-center min-h-[60vh]">
        <div className="bg-white rounded-xl border border-slate-200 p-10 text-center max-w-sm">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-slate-900 mb-2">Scan Not Found</h2>
          <p className="text-slate-500 text-sm mb-6">This scan ID does not exist or has been removed.</p>
          <button onClick={() => navigate('/dashboard')} className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const isFailed    = scan.state === 'FAILED';
  const isRunning   = scan.state === 'RUNNING' || scan.state === 'QUEUED';
  const isCompleted = scan.state === 'COMPLETED';
  const scanError   = (scan as Record<string, unknown>)?.error as { message: string; error_type?: string; jenkins_console_url?: string } | null;

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => navigate('/dashboard')} className="flex items-center gap-2 text-slate-500 hover:text-slate-800 text-sm transition-colors">
              <ArrowLeft className="w-4 h-4" />
              Dashboard
            </button>
            <div>
              <h1 className="text-lg font-bold text-slate-900">Scan Status</h1>
              <p className="text-xs text-slate-400 font-mono">{scan.scan_id}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* WebSocket status indicator */}
            <div className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border ${
              wsConnected
                ? 'text-emerald-700 bg-emerald-50 border-emerald-200'
                : 'text-slate-500 bg-slate-50 border-slate-200'
            }`}>
              {wsConnected ? (
                <><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" /><Wifi className="w-3 h-3" /> Live</>
              ) : (
                <><WifiOff className="w-3 h-3" /> Polling</>
              )}
            </div>
            <button
              onClick={() => refetch()}
              disabled={isRefetching}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-slate-200 rounded-lg text-sm hover:bg-slate-50 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefetching ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {ApiError.getErrorMessage(error, 'Failed to load scan details')}
            </div>
          )}

          {/* Overview cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              {
                label: 'Status',
                content: (
                  <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${getStatusColor(scan.state)}`}>
                    {getStatusIcon(scan.state)}
                    {scan.state}
                  </span>
                ),
              },
              {
                label: 'Mode',
                content: <span className="text-slate-800 font-medium capitalize text-sm">{scan.scan_mode || '—'}</span>,
              },
              {
                label: 'Started',
                content: <span className="text-slate-700 text-sm">{scan.started_at ? new Date(scan.started_at).toLocaleString() : '—'}</span>,
              },
              {
                label: isRunning ? 'Elapsed' : 'Finished',
                content: isRunning
                  ? <ElapsedTime startedAt={scan.started_at} />
                  : <span className="text-slate-700 text-sm">{scan.finished_at ? new Date(scan.finished_at).toLocaleString() : '—'}</span>,
              },
            ].map(({ label, content }) => (
              <div key={label} className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">{label}</div>
                {content}
              </div>
            ))}
          </div>

          {/* Stage results */}
          <div>
            <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-3">
              Security Stages
            </h2>
            {stages.length > 0 ? (
              <div className="space-y-2">
                {stages.map((stage, i) => (
                  <div
                    key={i}
                    className={`flex items-start gap-3 border rounded-xl p-4 transition-colors ${
                      stage.status.toLowerCase().includes('fail')
                        ? 'border-red-200 bg-red-50'
                        : 'border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <span className={`p-1.5 rounded-lg border ${getStatusColor(stage.status)}`}>
                      {getStatusIcon(stage.status)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <div>
                          <p className="font-medium text-slate-900 text-sm">{stage.stage}</p>
                          <p className="text-xs text-slate-500 capitalize">{stage.status}</p>
                        </div>
                        {stage.artifact_url && (
                          <a href={stage.artifact_url} target="_blank" rel="noopener noreferrer"
                            className="flex items-center gap-1 text-blue-600 hover:text-blue-700 text-xs font-medium flex-shrink-0">
                            <ExternalLink className="w-3 h-3" />
                            Report
                          </a>
                        )}
                      </div>
                      {stage.summary && (
                        <div className={`mt-2 text-xs p-2.5 rounded-lg leading-relaxed ${
                          stage.status.toLowerCase().includes('fail')
                            ? 'bg-red-100 text-red-800 border border-red-200'
                            : 'bg-white text-slate-600 border border-slate-200'
                        }`}>
                          {stage.summary}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <StagesEmptyState scanState={scan.state} />
            )}
          </div>

          {/* Failure details */}
          {isFailed && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-5 space-y-4">
              <h3 className="font-semibold text-red-900 flex items-center gap-2 text-sm">
                <AlertCircle className="w-4 h-4" />
                Scan Failure Details
              </h3>

              {scanError && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-red-700">Error type:</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      scanError.error_type === 'TIMEOUT' ? 'bg-amber-100 text-amber-800' :
                      scanError.error_type === 'USER_CANCELLED' ? 'bg-blue-100 text-blue-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {scanError.error_type || 'UNKNOWN'}
                    </span>
                  </div>
                  <div className="bg-white border border-red-200 rounded-lg p-3 text-xs text-red-700 font-mono leading-relaxed">
                    {scanError.message}
                  </div>
                </div>
              )}

              {stages.filter(s => s.status.toLowerCase().includes('fail')).length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-red-800 mb-2">Failed stages:</p>
                  <div className="space-y-1.5">
                    {stages.filter(s => s.status.toLowerCase().includes('fail')).map((s, i) => (
                      <div key={i} className="bg-white border border-red-200 rounded-lg px-3 py-2 flex items-center gap-2">
                        <AlertCircle className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />
                        <span className="text-xs font-medium text-red-900">{s.stage}</span>
                        {s.summary && <span className="text-xs text-red-600 truncate">— {s.summary}</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex items-center gap-2 flex-wrap">
                <button onClick={() => setShowErrorModal(true)}
                  className="text-xs px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium">
                  View Full Details
                </button>
                {scanError?.jenkins_console_url && (
                  <a href={scanError.jenkins_console_url} target="_blank" rel="noopener noreferrer"
                    className="text-xs px-3 py-1.5 border border-red-300 text-red-700 rounded-lg hover:bg-red-100 flex items-center gap-1.5 font-medium">
                    <ExternalLink className="w-3 h-3" />
                    Jenkins Console
                  </a>
                )}
              </div>
            </div>
          )}

          {/* Completion banner */}
          {isCompleted && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl px-5 py-4 flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0" />
              <div>
                <p className="text-sm font-semibold text-emerald-900">Scan completed successfully</p>
                <p className="text-xs text-emerald-700">
                  All stages finished.
                  {scan.finished_at && ` Completed at ${new Date(scan.finished_at).toLocaleString()}.`}
                </p>
              </div>
            </div>
          )}

          {/* Action buttons */}
          {(isFailed || isRunning) && (
            <div className="flex items-center gap-3 pt-2 border-t border-slate-100">
              {isFailed && (
                <button onClick={() => setShowResetConfirm(true)} disabled={resetMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium disabled:opacity-50 transition-colors">
                  <RefreshCw className={`w-4 h-4 ${resetMutation.isPending ? 'animate-spin' : ''}`} />
                  {resetMutation.isPending ? 'Resetting…' : 'Reset & Retry'}
                </button>
              )}
              {isRunning && (
                <button onClick={() => setShowCancelConfirm(true)} disabled={cancelMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 text-sm font-medium disabled:opacity-50 transition-colors">
                  <XCircle className="w-4 h-4" />
                  {cancelMutation.isPending ? 'Cancelling…' : 'Cancel Scan'}
                </button>
              )}
            </div>
          )}

          <div className="pt-2 border-t border-slate-100">
            <button onClick={() => navigate('/dashboard')}
              className="text-sm text-slate-500 hover:text-slate-800 transition-colors">
              ← Back to Dashboard
            </button>
          </div>
        </div>
      </div>

      {/* Modals */}
      <ScanErrorModal isOpen={showErrorModal} onClose={() => setShowErrorModal(false)} error={scanError} />

      <ConfirmModal
        isOpen={showResetConfirm}
        onClose={() => setShowResetConfirm(false)}
        onConfirm={handleReset}
        isLoading={resetMutation.isPending}
        variant="info"
        title="Reset Scan"
        description="This will reset the scan state so you can trigger a new run. The current failure details will be cleared."
        confirmLabel="Reset & Retry"
      />

      <ConfirmModal
        isOpen={showCancelConfirm}
        onClose={() => setShowCancelConfirm(false)}
        onConfirm={handleCancel}
        isLoading={cancelMutation.isPending}
        variant="warning"
        title="Cancel Running Scan"
        description="Are you sure you want to cancel this scan? Any stages currently in progress will be stopped."
        confirmLabel="Cancel Scan"
        cancelLabel="Keep Running"
      />
    </div>
  );
};

export default ScanStatusPage;
