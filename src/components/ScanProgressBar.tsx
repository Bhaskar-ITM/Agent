import { Clock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { type ScanStage } from '../types';

interface ScanProgressBarProps {
  stages: ScanStage[];
  scanState: string;
  startedAt?: string;
  estimatedTotalMinutes?: number;
}

const STAGE_ORDER = [
  'git_checkout',
  'sonar_scanner',
  'sonar_quality_gate',
  'npm_pip_install',
  'dependency_check',
  'trivy_fs_scan',
  'docker_build',
  'docker_push',
  'trivy_image_scan',
  'nmap_scan',
  'zap_scan',
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

const STAGE_DURATIONS: Record<string, number> = {
  git_checkout: 60,
  sonar_scanner: 180,
  sonar_quality_gate: 120,
  npm_pip_install: 90,
  dependency_check: 150,
  trivy_fs_scan: 90,
  docker_build: 240,
  docker_push: 90,
  trivy_image_scan: 120,
  nmap_scan: 60,
  zap_scan: 300,
};

function getStageStatusIcon(status: string) {
  const statusLower = status.toLowerCase();
  if (statusLower.includes('pass') || statusLower.includes('completed')) {
    return <CheckCircle className="w-4 h-4 text-green-600" />;
  } else if (statusLower.includes('fail') || statusLower.includes('error')) {
    return <AlertCircle className="w-4 h-4 text-red-600" />;
  } else if (statusLower.includes('running') || statusLower.includes('progress')) {
    return <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />;
  } else if (statusLower.includes('skip')) {
    return <Clock className="w-4 h-4 text-yellow-600" />;
  }
  return <Clock className="w-4 h-4 text-gray-400" />;
}

function calculateProgress(stages: ScanStage[], totalStages: number): {
  completed: number;
  running: string | null;
  pending: number;
  percentage: number;
} {
  let completed = 0;
  let running: string | null = null;
  
  stages.forEach(stage => {
    const status = stage.status.toLowerCase();
    if (status.includes('pass') || status.includes('completed')) {
      completed++;
    } else if (status.includes('running') || status.includes('progress')) {
      running = stage.stage;
    }
  });

  const pending = totalStages - completed - (running ? 1 : 0);
  const percentage = totalStages > 0 ? Math.round((completed / totalStages) * 100) : 0;

  return { completed, running, pending, percentage };
}

function calculateETA(stages: ScanStage[]): string {
  // Calculate remaining time based on completed stages
  let completedTime = 0;
  
  stages.forEach(stage => {
    const status = stage.status.toLowerCase();
    if (status.includes('pass') || status.includes('completed') || 
        status.includes('fail') || status.includes('error')) {
      const stageDuration = STAGE_DURATIONS[stage.stage] || 60;
      completedTime += stageDuration;
    }
  });

  // Estimate total time
  const totalEstimatedTime = Object.values(STAGE_DURATIONS).reduce((a, b) => a + b, 0);
  const remainingTime = Math.max(0, totalEstimatedTime - completedTime);
  
  if (remainingTime === 0) return 'Completing...';
  
  const mins = Math.floor(remainingTime / 60);
  return mins > 0 ? `${mins} min remaining` : `${Math.round(remainingTime)} sec remaining`;
}

export function ScanProgressBar({ 
  stages, 
  scanState, 
}: ScanProgressBarProps) {
  const totalStages = STAGE_ORDER.length;
  const { completed, running, pending, percentage } = calculateProgress(stages, totalStages);
  const eta = calculateETA(stages);

  const isRunning = scanState === 'RUNNING' || scanState === 'QUEUED';
  const isComplete = scanState === 'COMPLETED';
  const isFailed = scanState === 'FAILED';

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-6 mb-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          {isRunning ? (
            <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
          ) : isComplete ? (
            <CheckCircle className="w-5 h-5 text-green-600" />
          ) : isFailed ? (
            <AlertCircle className="w-5 h-5 text-red-600" />
          ) : (
            <Clock className="w-5 h-5 text-gray-400" />
          )}
          <h3 className="text-lg font-semibold text-slate-900">
            {isRunning ? 'Scan in Progress' : isComplete ? 'Scan Completed' : isFailed ? 'Scan Failed' : 'Scan Status'}
          </h3>
        </div>
        <div className="text-sm text-slate-600">
          {isRunning && <span className="text-blue-600 font-medium">{eta}</span>}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2 text-sm">
          <span className="text-slate-600">
            {completed} of {totalStages} stages completed
          </span>
          <span className="font-medium text-slate-900">{percentage}%</span>
        </div>
        <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              isFailed ? 'bg-red-500' : isComplete ? 'bg-green-500' : 'bg-blue-600'
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      {/* Stage Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {STAGE_ORDER.map((stageId) => {
          const stageResult = stages.find(s => s.stage === stageId);
          const status = stageResult?.status || 'pending';
          const isCurrentRunning = running === stageId;

          return (
            <div
              key={stageId}
              className={`flex items-center gap-2 p-3 rounded-lg border ${
                isCurrentRunning
                  ? 'border-blue-300 bg-blue-50'
                  : status.toLowerCase().includes('pass')
                  ? 'border-green-200 bg-green-50'
                  : status.toLowerCase().includes('fail')
                  ? 'border-red-200 bg-red-50'
                  : 'border-slate-200 bg-slate-50'
              }`}
            >
              {getStageStatusIcon(status)}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-slate-900 truncate">
                  {STAGE_DISPLAY_NAMES[stageId] || stageId}
                </div>
                <div className="text-xs text-slate-600">
                  {stageResult?.status || 'Pending'}
                </div>
              </div>
              {stageResult?.summary && (
                <div className="text-xs text-slate-500 truncate max-w-[100px]">
                  {stageResult.summary}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Summary Stats */}
      <div className="mt-4 pt-4 border-t border-slate-200 grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold text-green-600">{completed}</div>
          <div className="text-xs text-slate-600">Completed</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-blue-600">{running ? 1 : 0}</div>
          <div className="text-xs text-slate-600">Running</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-slate-600">{pending}</div>
          <div className="text-xs text-slate-600">Pending</div>
        </div>
      </div>
    </div>
  );
}
