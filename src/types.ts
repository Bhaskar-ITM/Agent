export type ScanStatus = 'PENDING' | 'RUNNING' | 'PASSED' | 'FAILED' | 'SKIPPED';
export type ScanMode = 'AUTOMATED' | 'MANUAL';

export type ScanStage = {
  name: string;
  status: ScanStatus;
  reportUrl?: string;
};

export type Project = {
  id: string;
  name: string;
  gitUrl: string;
  branch: string;
  credentials: string;
  sonarKey: string;
  targetIp?: string;
  targetUrl?: string;
  lastScanStatus?: string;
  lastScanId?: string;
};

export type Scan = {
  id: string;
  projectId: string;
  mode: ScanMode;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  stages: ScanStage[];
  createdAt: string;
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
