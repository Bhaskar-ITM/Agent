export type ScanStatus = 'PENDING' | 'RUNNING' | 'PASSED' | 'FAILED' | 'SKIPPED' | 'PASS' | 'WARN';
export type ScanMode = 'automated' | 'manual';

export type ScanStage = {
  stage: string;
  status: string; // Using string to be more flexible with backend statuses
  summary?: string;
  artifact_url?: string;
};

export type Project = {
  project_id: string;
  name: string;
  git_url: string;
  branch: string;
  credentials_id: string;
  sonar_key: string;
  target_ip?: string;
  target_url?: string;
  last_scan_state?: string;
};

export type Scan = {
  scan_id: string;
  project_id: string;
  state: 'INITIAL' | 'WAITING' | 'IN PROGRESS' | 'FINISHED' | 'FAILED' | 'CANCELLED' | 'CREATED' | 'QUEUED' | 'RUNNING' | 'COMPLETED';
  started_at?: string;
  finished_at?: string;
  results?: ScanStage[];
};

export const FIXED_STAGES = [
  'Git Checkout',
  'Sonar Scanner',
  'Sonar Quality Gate',
  'NPM / PIP Install',
  'Dependency Check',
  'Trivy FS Scan',
  'Docker Build',
  'Docker Push',
  'Trivy Image Scan',
  'Nmap Scan',
  'ZAP Scan'
] as const;

export type StageName = typeof FIXED_STAGES[number];

export const STAGE_ID_MAP: Record<StageName, string> = {
  'Git Checkout': 'git_checkout',
  'Sonar Scanner': 'sonar_scanner',
  'Sonar Quality Gate': 'sonar_quality_gate',
  'NPM / PIP Install': 'npm_pip_install',
  'Dependency Check': 'dependency_check',
  'Trivy FS Scan': 'trivy_fs_scan',
  'Docker Build': 'docker_build',
  'Docker Push': 'docker_push',
  'Trivy Image Scan': 'trivy_image_scan',
  'Nmap Scan': 'nmap_scan',
  'ZAP Scan': 'zap_scan'
};
