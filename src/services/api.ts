import axios from 'axios';
import { FIXED_STAGES } from '../types';
import type { Project, Scan, ScanStage, ScanMode } from '../types';

const API_BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  projects: {
    list: async (): Promise<Project[]> => {
      // For now, backend doesn't have list endpoint in skeleton, so we use a mock or implement it
      // Actually, I'll add the list endpoint to the backend to be complete
      const response = await apiClient.get('/projects');
      return response.data;
    },
    get: async (id: string): Promise<Project | undefined> => {
      const response = await apiClient.get(`/projects/${id}`);
      return response.data;
    },
    create: async (project: Omit<Project, 'id'>): Promise<Project> => {
      const response = await apiClient.post('/projects', project);
      return response.data;
    }
  },
  scans: {
    get: async (id: string): Promise<Scan | undefined> => {
      const response = await apiClient.get(`/scans/${id}`);
      const scanData = response.data;

      // Map backend ScanResponse to frontend Scan type
      const scan: Scan = {
        id: scanData.scanId,
        projectId: scanData.projectId,
        mode: scanData.mode,
        status: scanData.state, // state -> status
        stages: scanData.selectedStages.map((name: string) => ({
          name,
          status: 'PENDING'
        })),
        createdAt: scanData.createdAt
      };

      // Since the backend skeleton doesn't track stage progress yet,
      // we maintain the frontend simulation if the scan is RUNNING
      if (scan.status === 'RUNNING') {
        const now = new Date().getTime();
        const start = new Date(scan.createdAt).getTime();
        const elapsed = (now - start) / 1000;

        let allFinished = true;
        scan.stages = FIXED_STAGES.map((name, index) => {
          // If Manual and not selected, it should be SKIPPED
          if (scan.mode === 'MANUAL' && !scanData.selectedStages.includes(name)) {
            return { name, status: 'SKIPPED' as const };
          }

          // Automated discovery simulation
          if (scan.mode === 'AUTOMATED') {
             // In a real app, this discovery would happen in Jenkins and be reported back
             // For now we simulate it here to keep the UI behavior
          }

          const stageStartTime = index * 5;
          if (elapsed > stageStartTime + 5) {
            return { name, status: 'PASSED' as const, reportUrl: '#' };
          } else if (elapsed > stageStartTime) {
            allFinished = false;
            return { name, status: 'RUNNING' as const };
          }
          allFinished = false;
          return { name, status: 'PENDING' as const };
        });

        // Note: We don't update the backend state here,
        // in a real system Jenkins would do that.
      } else if (scan.status === 'COMPLETED') {
         scan.stages = FIXED_STAGES.map(name => ({
           name,
           status: 'PASSED' as const,
           reportUrl: '#'
         }));
      }

      return scan;
    },
    trigger: async (projectId: string, mode: ScanMode, selectedStages?: string[]): Promise<Scan> => {
      const response = await apiClient.post('/scans', {
        projectId,
        mode,
        selectedStages
      });
      const scanData = response.data;

      return {
        id: scanData.scanId,
        projectId: scanData.projectId,
        mode: scanData.mode,
        status: scanData.state,
        stages: [],
        createdAt: scanData.createdAt
      };
    }
  }
};
