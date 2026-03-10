import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { Clock, CheckCircle, AlertCircle, XCircle, ChevronDown } from 'lucide-react';

export default function RecentScans() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const { data: scans = [] } = useQuery({
    queryKey: ['recent-scans'],
    queryFn: async () => {
      const allScans = await api.scans.list();
      return allScans.slice(0, 5);
    },
    refetchInterval: 30000,
  });

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const getStatusIcon = (state: string) => {
    switch (state) {
      case 'COMPLETED': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'FAILED': return <AlertCircle className="w-4 h-4 text-red-600" />;
      case 'CANCELLED': return <XCircle className="w-4 h-4 text-blue-600" />;
      case 'RUNNING': return <Clock className="w-4 h-4 text-yellow-600 animate-pulse" />;
      default: return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const handleScanClick = (scanId: string) => {
    navigate(`/scans/${scanId}`);
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
      >
        <Clock className="w-4 h-4" />
        <span>Recent Scans</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white border border-slate-200 rounded-lg shadow-lg z-50">
          <div className="p-3 border-b border-slate-200">
            <h3 className="text-sm font-semibold text-slate-900">Recent Scans</h3>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {scans.length === 0 ? (
              <div className="p-4 text-center text-sm text-slate-500">
                No recent scans
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {scans.map((scan: any) => (
                  <button
                    key={scan.scan_id}
                    onClick={() => handleScanClick(scan.scan_id)}
                    className="w-full p-3 hover:bg-slate-50 transition-colors text-left"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(scan.state)}
                        <span className="text-xs font-medium text-slate-900">{scan.state}</span>
                      </div>
                      <span className="text-xs text-slate-500">
                        {scan.created_at ? new Date(scan.created_at).toLocaleDateString() : '-'}
                      </span>
                    </div>
                    <div className="text-xs text-slate-600 font-mono">
                      Scan: {scan.scan_id.slice(0, 12)}...
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      Project: {scan.project_id.slice(0, 12)}...
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="p-2 border-t border-slate-200">
            <button
              onClick={() => {
                navigate('/scans');
                setIsOpen(false);
              }}
              className="w-full text-center text-sm text-blue-600 hover:text-blue-700 py-2 rounded hover:bg-blue-50 transition-colors"
            >
              View All Scans
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
