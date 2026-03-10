import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { Clock, CheckCircle, AlertCircle, XCircle, Loader2, ExternalLink } from 'lucide-react';

export default function AllScansPage() {
  const navigate = useNavigate();
  
  const { data: scans = [], isLoading, error } = useQuery({
    queryKey: ['all-scans'],
    queryFn: () => api.scans.list(),
    refetchInterval: 10000,
  });

  const getStatusIcon = (state: string) => {
    switch (state) {
      case 'COMPLETED': return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'FAILED': return <AlertCircle className="w-5 h-5 text-red-600" />;
      case 'CANCELLED': return <XCircle className="w-5 h-5 text-blue-600" />;
      case 'RUNNING': return <Clock className="w-5 h-5 text-yellow-600 animate-pulse" />;
      default: return <Clock className="w-5 h-5 text-slate-400" />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        <span className="ml-2 text-slate-600">Loading scan history...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
        Failed to load scan history. Please try again.
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">All Scans</h1>
        <p className="text-slate-600 mt-1">View all security scans across all projects</p>
      </div>

      {scans.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center">
          <AlertCircle className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">No scans found</h3>
          <p className="text-slate-600 mb-6">Create a project and run your first scan to get started!</p>
          <button
            onClick={() => navigate('/projects/create')}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Create Project
          </button>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50 border-b">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase">Status</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase">Scan ID</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase">Project ID</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase">Mode</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase">Started</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase">Duration</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {scans.map((scan: any) => (
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
                  <td className="px-6 py-4">
                    <button
                      onClick={() => navigate(`/projects/${scan.project_id}`)}
                      className="text-sm text-slate-600 hover:text-slate-900 font-mono"
                    >
                      {scan.project_id.slice(0, 8)}...
                    </button>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-xs bg-slate-100 text-slate-700 px-2 py-1 rounded-full">
                      {scan.scan_mode || 'AUTOMATED'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600">
                    {scan.created_at ? new Date(scan.created_at).toLocaleString() : '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600">
                    {scan.finished_at && scan.created_at
                      ? Math.round((new Date(scan.finished_at).getTime() - new Date(scan.created_at).getTime()) / 1000 / 60) + 'm'
                      : scan.state === 'RUNNING' ? 'In progress' : '-'
                    }
                  </td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => navigate(`/scans/${scan.scan_id}`)}
                      className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
