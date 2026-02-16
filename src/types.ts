export type ScanStatus = 'PENDING' | 'RUNNING' | 'PASSED' | 'FAILED' | 'SKIPPED';
export type ScanMode = 'AUTOMATED' | 'MANUAL';

export type ScanStage = {
  stage: string;
  status: ScanStatus;
  summary?: string;
  artifact_url?: string;
  findings?: Record<string, number>;
  artifacts?: string[];
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
  state: 'CREATED' | 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  started_at?: string;
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
