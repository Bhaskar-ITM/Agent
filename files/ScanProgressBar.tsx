import { useState, useEffect } from 'react';
import { Clock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { type ScanStage } from '../types';

interface ScanProgressBarProps {
  stages: ScanStage[];
  scanState: string;
  selectedStages?: string[]; // from scan.selected_stages — used to calculate correct denominator
  startedAt?: string;
}

const STAGE_ORDER = [
  'git_checkout', 'sonar_scanner', 'sonar_quality_gate', 'npm_pip_install',
  'dependency_check', 'trivy_fs_scan', 'docker_build', 'docker_push',
  'trivy_image_scan', 'nmap_scan', 'zap_scan',
];

const STAGE_DISPLAY_NAMES: Record<string, string> = {
  git_checkout: 'Git Checkout',
  sonar_scanner: 'Sonar Scanner',
  sonar_quality_gate: 'Quality Gate',
  npm_pip_install: 'Install Dependencies',
  dependency_check: 'Dependency Check',
  trivy_fs_scan: 'Trivy FS Scan',
  docker_build: 'Docker Build',
  docker_push: 'Docker Push',
  trivy_image_scan: 'Trivy Image Scan',
  nmap_scan: 'Nmap Scan',
  zap_scan: 'ZAP Scan',
};

function getStageStatusIcon(status: string) {
  const s = status.toLowerCase();
  if (s === 'pass' || s === 'passed' || s === 'completed') return <CheckCircle className="w-4 h-4 text-emerald-600" />;
  if (s === 'fail' || s === 'failed' || s === 'error') return <AlertCircle className="w-4 h-4 text-red-600" />;
  if (s === 'running' || s === 'in progress') return <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />;
  return <Clock className="w-4 h-4 text-slate-400" />;
}

function ElapsedTimer({ startedAt }: { startedAt: string }) {
  const [elapsed, setElapsed] = useState('');
  useEffect(() => {
    const tick = () => {
      const secs = Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000);
      const m = Math.floor(secs / 60);
      const s = secs % 60;
      setElapsed(m > 0 ? `${m}m ${s.toString().padStart(2, '0')}s` : `${s}s`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [startedAt]);
  return <span className="text-blue-600 font-medium text-sm">{elapsed}</span>;
}

export function ScanProgressBar({ stages, scanState, selectedStages, startedAt }: ScanProgressBarProps) {
  // Fix: use selectedStages.length as denominator for manual scans; fall back to all stages
  const activeStageIds =
    selectedStages && selectedStages.length > 0
      ? selectedStages
      : STAGE_ORDER;

  const totalStages = activeStageIds.length;

  let completed = 0;
  let runningStageId: string | null = null;

  stages.forEach(stage => {
    const s = stage.status.toLowerCase();
    if (s === 'pass' || s === 'passed' || s === 'completed') completed++;
    else if (s === 'running' || s === 'in progress') runningStageId = stage.stage;
  });

  const percentage = totalStages > 0 ? Math.round((completed / totalStages) * 100) : 0;
  const pending = Math.max(0, totalStages - completed - (runningStageId ? 1 : 0));

  const isRunning   = scanState === 'RUNNING' || scanState === 'QUEUED';
  const isCompleted = scanState === 'COMPLETED';
  const isFailed    = scanState === 'FAILED';

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 mb-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          {isRunning   && <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />}
          {isCompleted && <CheckCircle className="w-5 h-5 text-emerald-600" />}
          {isFailed    && <AlertCircle className="w-5 h-5 text-red-600" />}
          {!isRunning && !isCompleted && !isFailed && <Clock className="w-5 h-5 text-slate-400" />}
          <h3 className="text-base font-semibold text-slate-900">
            {isRunning ? 'Scan in Progress' : isCompleted ? 'Scan Completed' : isFailed ? 'Scan Failed' : 'Scan Status'}
          </h3>
        </div>
        <div className="text-sm text-slate-500">
          {isRunning && startedAt && <ElapsedTimer startedAt={startedAt} />}
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1.5 text-sm">
          <span className="text-slate-500">{completed} of {totalStages} stages</span>
          <span className="font-semibold text-slate-800">{percentage}%</span>
        </div>
        <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              isFailed ? 'bg-red-500' : isCompleted ? 'bg-emerald-500' : 'bg-blue-600'
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      {/* Stage grid — only show stages relevant to this scan */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
        {activeStageIds.map(stageId => {
          const result = stages.find(s => s.stage === stageId);
          const status = result?.status ?? 'pending';
          const isCurrent = runningStageId === stageId;

          return (
            <div
              key={stageId}
              className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg border text-sm transition-colors ${
                isCurrent
                  ? 'border-blue-300 bg-blue-50'
                  : status.toLowerCase() === 'pass' || status.toLowerCase() === 'passed'
                  ? 'border-emerald-200 bg-emerald-50'
                  : status.toLowerCase() === 'fail' || status.toLowerCase() === 'failed'
                  ? 'border-red-200 bg-red-50'
                  : 'border-slate-200 bg-slate-50'
              }`}
            >
              {getStageStatusIcon(status)}
              <div className="min-w-0">
                <div className="font-medium text-slate-800 truncate text-xs">
                  {STAGE_DISPLAY_NAMES[stageId] ?? stageId}
                </div>
                <div className="text-xs text-slate-500 capitalize">{result?.status ?? 'Pending'}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      <div className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-xl font-bold text-emerald-600">{completed}</div>
          <div className="text-xs text-slate-500">Completed</div>
        </div>
        <div>
          <div className="text-xl font-bold text-blue-600">{runningStageId ? 1 : 0}</div>
          <div className="text-xs text-slate-500">Running</div>
        </div>
        <div>
          <div className="text-xl font-bold text-slate-400">{pending}</div>
          <div className="text-xs text-slate-500">Pending</div>
        </div>
      </div>
    </div>
  );
}
