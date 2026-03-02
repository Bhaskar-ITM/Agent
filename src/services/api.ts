import axios from 'axios';
import type { Project, Scan, ScanStage, ScanMode, StageId } from '../types';

const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  } else {
    // Fallback to API Key for external compatibility if no token exists
    const apiKey = localStorage.getItem('API_KEY') || import.meta.env.VITE_API_KEY;
    if (apiKey) {
      config.headers['X-API-Key'] = apiKey;
    }
  }
  return config;
});

export const api = {
  auth: {
    login: async (username: string, password: string): Promise<{ access_token: string, token_type: string }> => {
      // OAuth2 expects form-urlencoded
      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);

      const response = await apiClient.post('/auth/login', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      return response.data;
    },
    register: async (username: string, password: string, email?: string): Promise<{ username: string }> => {
      const response = await apiClient.post('/auth/register', {
        username,
        password,
        email: email || `${username}@example.com`
      });
      return response.data;
    }
  },
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
    trigger: async (project_id: string, scan_mode: ScanMode, selected_stages?: StageId[]): Promise<Scan> => {
      const response = await apiClient.post('/scans', {
        project_id,
        scan_mode,
        selected_stages
      });
      return response.data;
    }
  }
};
