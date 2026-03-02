import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, AlertCircle, CheckCircle, Clock, ExternalLink } from 'lucide-react';
import { api } from '../services/api';
import { type Scan, type ScanStage } from '../types';

const ScanStatusPage = () => {
  const { id: scanId } = useParams();
  const navigate = useNavigate();
  const [scan, setScan] = useState<Scan | null>(null);
  const [stages, setStages] = useState<ScanStage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchScanData = useCallback(async () => {
    if (!scanId) return;
    
    try {
      setIsRefreshing(true);
      const scanData = await api.scans.get(scanId);
      if (scanData) {
        setScan(scanData);
        
        if (scanData.results) {
          setStages(scanData.results);
        } else {
          // Fetch results separately if not included
          const resultsData = await api.scans.getResults(scanId);
          setStages(resultsData);
        }
      }
    } catch (err) {
      console.error('Failed to fetch scan data:', err);
      setError('Failed to load scan details');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [scanId]);

  useEffect(() => {
    fetchScanData();
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchScanData, 10000);
    return () => clearInterval(interval);
  }, [scanId, fetchScanData]);

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
          <RefreshCw className="animate-spin h-6 w-6 text-blue-600" />
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
              onClick={fetchScanData}
              disabled={isRefreshing}
              className="flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              {error}
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
                  <div key={index} className="border border-slate-200 rounded-lg p-4 hover:bg-slate-50 transition-colors">
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
                      <div className="text-sm text-slate-700 bg-slate-50 p-3 rounded">
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