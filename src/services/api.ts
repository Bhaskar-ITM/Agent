import axios from 'axios';
import type { Project, Scan, ScanStage, ScanMode } from '../types';

const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  projects: {
    list: async (): Promise<Project[]> => {
      try {
        const response = await apiClient.get('/projects');
        console.log('API projects.list response:', response.data);
        return Array.isArray(response.data) ? response.data : [];
      } catch (err) {
        console.error('API projects.list error:', err);
        return [];
      }
    },
    get: async (id: string): Promise<Project | undefined> => {
      const response = await apiClient.get(`/projects/${id}`);
      return response.data;
    },
    create: async (project: Omit<Project, 'project_id'>): Promise<Project> => {
      const response = await apiClient.post('/projects', project);
      return response.data;
    }
  },
  scans: {
    get: async (id: string): Promise<Scan | undefined> => {
      const response = await apiClient.get(`/scans/${id}`);
      return response.data;
    },
    getResults: async (id: string): Promise<ScanStage[]> => {
      const response = await apiClient.get(`/scans/${id}/results`);
      return response.data.results;
    },
    trigger: async (project_id: string, mode: ScanMode, selected_stages?: string[], target_url?: string): Promise<Scan> => {
      const response = await apiClient.post('/scans', {
        project_id,
        mode,
        selected_stages,
        target_url
      });
      return response.data;
    },
    queue: async (scan_id: string): Promise<void> => {
      await apiClient.post(`/scans/${scan_id}/queue`);
    }
  }
};
