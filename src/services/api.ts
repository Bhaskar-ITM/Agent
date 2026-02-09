import { FIXED_STAGES } from '../types';
import type { Project, Scan, ScanStage, ScanMode } from '../types';

const STORAGE_KEY_PROJECTS = 'devsecops_projects';
const STORAGE_KEY_SCANS = 'devsecops_scans';

let projectsCache: Project[] | null = null;
let scansCache: Scan[] | null = null;

const getProjects = (): Project[] => {
  if (projectsCache) return projectsCache;
  const data = localStorage.getItem(STORAGE_KEY_PROJECTS);
  projectsCache = data ? JSON.parse(data) : [];
  return projectsCache!;
};

const getScans = (): Scan[] => {
  if (scansCache) return scansCache;
  const data = localStorage.getItem(STORAGE_KEY_SCANS);
  scansCache = data ? JSON.parse(data) : [];
  return scansCache!;
};

const saveProjects = (projects: Project[]) => {
  projectsCache = projects;
  localStorage.setItem(STORAGE_KEY_PROJECTS, JSON.stringify(projects));
};

const saveScans = (scans: Scan[]) => {
  scansCache = scans;
  localStorage.setItem(STORAGE_KEY_SCANS, JSON.stringify(scans));
};

export const api = {
  projects: {
    list: async () => {
      return [...getProjects()];
    },
    get: async (id: string) => {
      const project = getProjects().find(p => p.id === id);
      return project ? { ...project } : undefined;
    },
    create: async (project: Omit<Project, 'id'>) => {
      const projects = getProjects();
      const newProject = { ...project, id: Math.random().toString(36).substr(2, 9) } as Project;
      projects.push(newProject);
      saveProjects(projects);
      return newProject;
    }
  },
  scans: {
    get: async (id: string) => {
      const scan = getScans().find(s => s.id === id);
      if (scan && scan.status === 'RUNNING') {
        const now = new Date().getTime();
        const start = new Date(scan.createdAt).getTime();
        const elapsed = (now - start) / 1000;

        let allFinished = true;
        const updatedStages = scan.stages.map((stage, index) => {
          if (stage.status === 'SKIPPED') return stage;

          // Automated mode discovery/skipping simulation
          if (scan.mode === 'AUTOMATED') {
            const project = getProjects().find(p => p.id === scan.projectId);
            if (stage.name === 'Nmap Scan' && !project?.targetIp) return { ...stage, status: 'SKIPPED' as const };
            if (stage.name === 'ZAP Scan' && !project?.targetUrl) return { ...stage, status: 'SKIPPED' as const };
          }

          const stageStartTime = index * 5;
          if (elapsed > stageStartTime + 5) {
            return { ...stage, status: 'PASSED' as const, reportUrl: '#' };
          } else if (elapsed > stageStartTime) {
            allFinished = false;
            return { ...stage, status: 'RUNNING' as const };
          }
          allFinished = false;
          return stage;
        });

        if (allFinished) {
          scan.status = 'COMPLETED';
          const projects = getProjects();
          const project = projects.find(p => p.id === scan.projectId);
          if (project) {
            project.lastScanStatus = 'PASSED';
            project.lastScanId = scan.id;
            saveProjects(projects);
          }
        }
        scan.stages = updatedStages;
        saveScans(getScans());
      }
      return scan ? { ...scan } : undefined;
    },
    trigger: async (projectId: string, mode: ScanMode, selectedStages?: string[]) => {
      const scans = getScans();
      const stages: ScanStage[] = FIXED_STAGES.map(name => {
        if (mode === 'MANUAL' && selectedStages && !selectedStages.includes(name)) {
          return { name, status: 'SKIPPED' as const };
        }
        return { name, status: 'PENDING' as const };
      });

      const newScan: Scan = {
        id: Math.random().toString(36).substr(2, 9),
        projectId,
        mode,
        status: 'RUNNING',
        stages,
        createdAt: new Date().toISOString()
      };
      scans.push(newScan);
      saveScans(scans);

      const projects = getProjects();
      const project = projects.find(p => p.id === projectId);
      if (project) {
        project.lastScanStatus = 'RUNNING';
        project.lastScanId = newScan.id;
        saveProjects(projects);
      }

      return newScan;
    }
  }
};
