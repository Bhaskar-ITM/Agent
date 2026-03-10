import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { ArrowLeft, Clock, CheckCircle, AlertCircle, XCircle, ExternalLink } from 'lucide-react';
import Breadcrumb from '../components/Breadcrumb';

export default function ScanHistoryPage() {
  const { id: projectId } = useParams();
  const navigate = useNavigate();
  
  const { data: history = [], isLoading, error } = useQuery({
    queryKey: ['scan-history', projectId],
    queryFn: () => api.projects.getScanHistory(projectId!),
    refetchInterval: 10000,
    enabled: !!projectId,
  });

  const getStatusIcon = (state: string) => {
    switch (state) {
      case 'COMPLETED': return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'FAILED': return <AlertCircle className="w-5 h-5 text-red-600" />;
      case 'CANCELLED': return <XCircle className="w-5 h-5 text-blue-600" />;
      default: return <Clock className="w-5 h-5 text-yellow-600" />;
    }
  };

  if (isLoading) return <div className="p-8">Loading history...</div>;

  if (error) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          Failed to load scan history. Please try again.
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <Breadcrumb
        items={[
          { label: 'Projects', to: '/dashboard' },
          { label: projectId?.slice(0, 8) + '...', to: `/projects/${projectId}` },
          { label: 'Scan History' }
        ]}
      />
      <button
        onClick={() => navigate(`/projects/${projectId}`)}
        className="flex items-center gap-2 text-slate-600 hover:text-slate-900 mb-6"
      >
        <ArrowLeft className="w-5 h-5" />
        Back to Project
      </button>

      <h1 className="text-2xl font-bold text-slate-900 mb-6">Scan History</h1>

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500">Status</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500">Scan ID</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500">Started</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500">Duration</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500">Retries</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {history.map((scan: any) => (
              <tr key={scan.scan_id} className="hover:bg-slate-50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(scan.state)}
                    <span className="text-sm font-medium">{scan.state}</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <button
                    onClick={() => navigate(`/scans/${scan.scan_id}`)}
                    className="text-sm text-blue-600 hover:text-blue-800 font-mono flex items-center gap-1"
                  >
                    {scan.scan_id.slice(0, 8)}...
                    <ExternalLink className="w-3 h-3" />
                  </button>
                </td>
                <td className="px-6 py-4 text-sm text-slate-600">
                  {new Date(scan.created_at).toLocaleString()}
                </td>
                <td className="px-6 py-4 text-sm text-slate-600">
                  {scan.finished_at 
                    ? Math.round((new Date(scan.finished_at).getTime() - new Date(scan.created_at).getTime()) / 1000 / 60) + 'm'
                    : 'In progress'
                  }
                </td>
                <td className="px-6 py-4">
                  {scan.retry_count > 0 ? (
                    <span className="text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded-full">
                      {scan.retry_count} retries
                    </span>
                  ) : (
                    <span className="text-xs text-slate-400">-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {history.length === 0 && (
          <div className="text-center py-12 text-slate-500">
            No scan history yet
          </div>
        )}
      </div>
    </div>
  );
}

