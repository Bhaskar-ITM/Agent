import axios from 'axios';
import type { Project, Scan, ScanStage, ScanMode } from '../types';

const API_BASE_URL = '/api/v1';
const API_KEY = import.meta.env.VITE_API_KEY as string | undefined;

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
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
    list: async (): Promise<Scan[]> => {
      const response = await apiClient.get('/scans');
      return response.data;
    },
    get: async (id: string): Promise<Scan | undefined> => {
      const response = await apiClient.get(`/scans/${id}`);
      return response.data;
    },
    getResults: async (id: string): Promise<ScanStage[]> => {
      const response = await apiClient.get(`/scans/${id}/results`);
      return response.data.results;
    },
    trigger: async (project_id: string, scan_mode: ScanMode, selected_stages?: string[]): Promise<Scan> => {
      const response = await apiClient.post('/scans', {
        project_id,
        scan_mode,
        selected_stages
      });
      return response.data;
    }
  }
};
