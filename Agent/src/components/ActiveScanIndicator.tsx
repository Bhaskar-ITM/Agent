import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { Activity } from 'lucide-react';

export default function ActiveScanIndicator() {
  const navigate = useNavigate();

  const { data: scans = [] } = useQuery({
    queryKey: ['active-scans'],
    queryFn: async () => {
      const allScans = await api.scans.list();
      return allScans.filter((scan: any) => scan.state === 'RUNNING');
    },
    refetchInterval: 5000,
  });

  if (scans.length === 0) return null;

  const activeScan = scans[0] as any;

  return (
    <button
      onClick={() => navigate(`/scans/${activeScan.scan_id}`)}
      className="flex items-center gap-2 px-3 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
    >
      <Activity className="w-4 h-4 animate-pulse" />
      <span>Active Scan</span>
      <span className="text-xs bg-blue-200 px-2 py-0.5 rounded-full">
        {scans.length}
      </span>
    </button>
  );
}
