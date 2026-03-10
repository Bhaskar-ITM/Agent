import { useState, useCallback, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, RefreshCw, AlertCircle, CheckCircle, Clock, ExternalLink, XCircle, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import { ApiError } from '../utils/apiError';
import { type ScanStage } from '../types';
import { useScanReset, useScanCancel } from '../hooks/useScanReset';
import { useScanWebSocket } from '../hooks/useScanWebSocket';
import { ScanErrorModal } from '../components/ScanErrorModal';
import { notificationService } from '../services/notifications';

const ScanStatusPage = () => {
  const { id: scanId } = useParams();
  const navigate = useNavigate();
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [notificationPermissionRequested, setNotificationPermissionRequested] = useState(false);
  const resetMutation = useScanReset();
  const cancelMutation = useScanCancel();

  const fetchScanData = useCallback(async () => {
    if (!scanId) return null;
    const scanData = await api.scans.get(scanId);
    if (!scanData) return null;

    let results: ScanStage[] = [];
    if (scanData.results) {
      results = scanData.results;
    } else {
      try {
        results = await api.scans.getResults(scanId);
      } catch {
        // Results may not be ready yet
        results = [];
      }
    }

    return { scan: scanData, stages: results };
  }, [scanId]);

  const {
    data: scanData,
    isLoading,
    isRefetching,
    refetch,
    error
  } = useQuery({
    queryKey: ['scan', scanId],
    queryFn: fetchScanData,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Stop polling when scan is complete or failed
      if (!data || data.scan.state === 'COMPLETED' || data.scan.state === 'FAILED') {
        return false;
      }
      return 2000; // Poll every 2 seconds for running scans
    },
    retry: 3,
    retryDelay: 1000,
  });

  const scan = scanData?.scan || null;
  const stages = scanData?.stages || [];

  // WebSocket for real-time updates (Phase 3.1)
  useScanWebSocket(scanId, undefined, {
    onMessage: (message) => {
      console.log('Real-time update received:', message);
      // Refetch to get latest data
      refetch();
    },
    onOpen: () => {
      console.log('WebSocket connected for real-time updates');
    },
  });

  // Request notification permission and show notifications (Phase 3.2)
  useEffect(() => {
    if (!notificationPermissionRequested && notificationService.isSupported()) {
      notificationService.requestPermission();
      setNotificationPermissionRequested(true);
    }
  }, [notificationPermissionRequested]);

  // Show notification when scan completes
  useEffect(() => {
    if (scan && (scan.state === 'COMPLETED' || scan.state === 'FAILED') && notificationService.hasPermission()) {
      notificationService.showScanComplete(scan.scan_id, scan.state);
    }
  }, [scan?.state]);

  const getStatusColor = (status: string) => {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('running') || statusLower.includes('in progress')) {
      return 'text-blue-600 bg-blue-50';
    } else if (statusLower.includes('passed') || statusLower.includes('completed') || statusLower.includes('pass')) {
      return 'text-green-600 bg-green-50';
    } else if (statusLower.includes('failed') || statusLower.includes('error') || statusLower.includes('fail')) {
      return 'text-red-600 bg-red-50';
    } else if (statusLower.includes('skipped')) {
      return 'text-yellow-600 bg-yellow-50';
    } else {
      return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusIcon = (status: string) => {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('running') || statusLower.includes('in progress')) {
      return <Clock className="w-4 h-4 animate-pulse" />;
    } else if (statusLower.includes('passed') || statusLower.includes('completed') || statusLower.includes('pass')) {
      return <CheckCircle className="w-4 h-4" />;
    } else if (statusLower.includes('failed') || statusLower.includes('error') || statusLower.includes('fail')) {
      return <AlertCircle className="w-4 h-4" />;
    } else {
      return <Clock className="w-4 h-4" />;
    }
  };

  if (isLoading && !scan) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-sm p-8 flex items-center gap-4">
          <Loader2 className="animate-spin h-6 w-6 text-blue-600" />
          <span className="text-slate-700">Loading scan details...</span>
        </div>
      </div>
    );
  }

  if (!scan) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-sm p-8 text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-slate-900 mb-2">Scan Not Found</h2>
          <p className="text-slate-600 mb-6">The scan you're looking for doesn't exist or has been removed.</p>
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
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                Back to Dashboard
              </button>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Scan Status</h1>
                <p className="text-slate-600">Scan ID: {scan.scan_id}</p>
              </div>
            </div>
            <button
              onClick={() => refetch()}
              disabled={isRefetching}
              className="flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isRefetching ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              {ApiError.getErrorMessage(error, 'Failed to load scan details')}
            </div>
          )}

          {/* Scan Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-slate-50 rounded-lg p-4">
              <div className="text-sm text-slate-600 mb-1">Status</div>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded-full text-sm font-medium ${getStatusColor(scan.state)}`}>
                  {getStatusIcon(scan.state)}
                  <span className="ml-1">{scan.state}</span>
                </span>
              </div>
            </div>
            <div className="bg-slate-50 rounded-lg p-4">
              <div className="text-sm text-slate-600 mb-1">Project ID</div>
              <div className="font-medium">{scan.project_id}</div>
            </div>
            <div className="bg-slate-50 rounded-lg p-4">
              <div className="text-sm text-slate-600 mb-1">Started At</div>
              <div className="font-medium">{scan.started_at ? new Date(scan.started_at).toLocaleString() : 'Not started'}</div>
            </div>
            <div className="bg-slate-50 rounded-lg p-4">
              <div className="text-sm text-slate-600 mb-1">Finished At</div>
              <div className="font-medium">{scan.finished_at ? new Date(scan.finished_at).toLocaleString() : 'In progress'}</div>
            </div>
          </div>

          {/* Stages */}
          <div>
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Security Stages</h2>
            <div className="space-y-3">
              {stages.length > 0 ? (
                stages.map((stage, index) => (
                  <div 
                    key={index} 
                    className={`border rounded-lg p-4 transition-colors ${
                      stage.status.toLowerCase().includes('fail') 
                        ? 'border-red-300 bg-red-50' 
                        : 'border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span className={`p-1 rounded ${getStatusColor(stage.status)}`}>
                          {getStatusIcon(stage.status)}
                        </span>
                        <div>
                          <div className="font-medium text-slate-900">{stage.stage}</div>
                          <div className="text-sm text-slate-600">{stage.status}</div>
                        </div>
                      </div>
                      {stage.artifact_url && (
                        <a
                          href={stage.artifact_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 text-blue-600 hover:text-blue-700 text-sm"
                        >
                          <ExternalLink className="w-4 h-4" />
                          View Report
                        </a>
                      )}
                    </div>
                    {stage.summary && (
                      <div className={`text-sm p-3 rounded mt-2 ${
                        stage.status.toLowerCase().includes('fail')
                          ? 'bg-red-100 text-red-800 border border-red-200'
                          : 'bg-slate-50 text-slate-700'
                      }`}>
                        {stage.summary}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-500">
                  No scan results available yet. The scan may still be in progress.
                </div>
              )}
            </div>
          </div>

          {/* Failure Details Section */}
          {scan && scan.state === 'FAILED' && (
            <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-red-900 mb-4 flex items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                Scan Failure Details
              </h3>
              
              {/* Show error from scan object */}
              {(scan as any)?.error && (
                <div className="mb-6">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="text-sm font-medium text-red-800">
                      Error Type: {(scan as any).error.error_type || 'UNKNOWN_ERROR'}
                    </div>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                      (scan as any).error.error_type === 'TIMEOUT' ? 'bg-yellow-100 text-yellow-800' :
                      (scan as any).error.error_type === 'PIPELINE_ERROR' ? 'bg-red-100 text-red-800' :
                      (scan as any).error.error_type === 'USER_CANCELLED' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {(scan as any).error.error_type || 'UNKNOWN_ERROR'}
                    </div>
                  </div>
                  <div className="bg-white border border-red-200 rounded p-4 shadow-sm">
                    <div className="text-sm text-red-700 leading-relaxed">
                      {(scan as any).error.message || 'Unknown error occurred'}
                    </div>
                  </div>
                </div>
              )}

              {/* Show failed stages */}
              {stages.filter(s => s.status.toLowerCase().includes('fail')).length > 0 && (
                <div className="mb-6">
                  <div className="text-sm font-medium text-red-800 mb-3">Failed Stages:</div>
                  <div className="space-y-3">
                    {stages.filter(s => s.status.toLowerCase().includes('fail')).map((stage, idx) => (
                      <div key={idx} className="bg-white border border-red-200 rounded-lg p-4 shadow-sm">
                        <div className="flex items-center gap-2 mb-2">
                          <AlertCircle className="w-4 h-4 text-red-500" />
                          <div className="font-medium text-red-900">{stage.stage}</div>
                        </div>
                        {stage.summary && (
                          <div className="text-sm text-red-700 mt-1">
                            {stage.summary}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Common failure reasons */}
              <div className="mb-6">
                <div className="text-sm font-medium text-red-800 mb-2">Common Causes:</div>
                <ul className="text-sm text-red-700 space-y-1 list-disc list-inside">
                  <li>Quality Gate timeout - SonarQube analysis took too long</li>
                  <li>Git credentials issue - Check credentials_id in project settings</li>
                  <li>SonarQube server unavailable - Check server connection</li>
                  <li>Resource constraints - Jenkins ran out of memory or disk space</li>
                </ul>
              </div>

              {/* Action buttons */}
              <div className="mt-4 flex gap-3">
                <button
                  onClick={() => setShowErrorModal(true)}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium"
                >
                  View Full Error Details
                </button>
                {(scan as any)?.error?.jenkins_console_url && (
                  <a
                    href={(scan as any).error.jenkins_console_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-100 text-sm font-medium flex items-center gap-2"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Open Jenkins Console
                  </a>
                )}
              </div>
            </div>
          )}

          {/* Reset and Cancel Buttons */}
          {scan && (scan.state === 'FAILED' || scan.state === 'RUNNING') && (
            <div className="mt-6 flex gap-4">
              {scan.state === 'FAILED' && (
                <button
                  onClick={() => {
                    if (confirm('Reset this scan and allow retry?')) {
                      resetMutation.mutate(scan.scan_id, {
                        onSuccess: () => {
                          refetch();
                        },
                        onError: (err: unknown) => {
                          const errorMsg = err as { message?: string };
                          alert(`Failed to reset: ${errorMsg.message || 'Unknown error'}`);
                        }
                      });
                    }
                  }}
                  disabled={resetMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  <RefreshCw className={`w-4 h-4 ${resetMutation.isPending ? 'animate-spin' : ''}`} />
                  {resetMutation.isPending ? 'Resetting...' : 'Reset & Retry'}
                </button>
              )}

              {scan.state === 'RUNNING' && (
                <button
                  onClick={() => {
                    if (confirm('Cancel this running scan?')) {
                      cancelMutation.mutate(scan.scan_id, {
                        onSuccess: () => {
                          refetch();
                        }
                      });
                    }
                  }}
                  disabled={cancelMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 disabled:opacity-50"
                >
                  <XCircle className="w-4 h-4" />
                  Cancel Scan
                </button>
              )}
            </div>
          )}

          {/* Error Display Button */}
          {(scan as any)?.error && (
            <div className="mt-6">
              <button
                onClick={() => setShowErrorModal(true)}
                className="flex items-center gap-2 text-red-600 hover:text-red-700 font-medium"
              >
                <AlertCircle className="w-5 h-5" />
                View Error Details
              </button>
            </div>
          )}

          {/* Error Modal */}
          <ScanErrorModal
            isOpen={showErrorModal}
            onClose={() => setShowErrorModal(false)}
            error={(scan as any)?.error || null}
          />

          {/* Actions */}
          <div className="mt-8 flex gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScanStatusPage;