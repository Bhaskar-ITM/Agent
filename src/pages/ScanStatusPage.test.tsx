import { render, act } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ScanStatusPage from './ScanStatusPage';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { api } from '../services/api';
import type { Project, Scan } from '../types';

vi.mock('../services/api', () => ({
  api: {
    projects: {
      get: vi.fn(),
    },
    scans: {
      get: vi.fn(),
    }
  }
}));

describe('ScanStatusPage Polling Optimization', () => {
  const mockProject: Project = {
    id: 'proj1',
    name: 'Test Project',
    gitUrl: 'https://github.com/test/repo',
    branch: 'main',
    credentials: 'cred',
    sonarKey: 'sonar'
  };

  const mockRunningScan: Scan = {
    id: 'scan1',
    projectId: 'proj1',
    status: 'RUNNING',
    mode: 'AUTOMATED',
    createdAt: new Date().toISOString(),
    stages: [
      { name: 'Git Checkout', status: 'PASSED' },
      { name: 'Sonar Scanner', status: 'RUNNING' },
    ]
  };

  const mockCompletedScan: Scan = {
    id: 'scan1',
    projectId: 'proj1',
    status: 'COMPLETED',
    mode: 'AUTOMATED',
    createdAt: new Date().toISOString(),
    stages: [
      { name: 'Git Checkout', status: 'PASSED' },
      { name: 'Sonar Scanner', status: 'PASSED' },
    ]
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  it('stops polling once the scan is completed', async () => {
    vi.mocked(api.projects.get).mockResolvedValue(mockProject);

    vi.mocked(api.scans.get)
      .mockResolvedValueOnce(mockRunningScan)
      .mockResolvedValue(mockCompletedScan);

    await act(async () => {
      render(
        <MemoryRouter initialEntries={['/scans/scan1']}>
          <Routes>
            <Route path="/scans/:id" element={<ScanStatusPage />} />
          </Routes>
        </MemoryRouter>
      );
    });

    expect(api.scans.get).toHaveBeenCalledTimes(1);

    await act(async () => {
      vi.advanceTimersByTime(2000);
    });

    expect(api.scans.get).toHaveBeenCalledTimes(2);

    await act(async () => {
      vi.advanceTimersByTime(10000);
    });

    expect(api.scans.get).toHaveBeenCalledTimes(2);
  });

  it('performs exactly one fetch on mount', async () => {
    vi.mocked(api.projects.get).mockResolvedValue(mockProject);
    vi.mocked(api.scans.get).mockResolvedValue(mockCompletedScan);

    await act(async () => {
      render(
        <MemoryRouter initialEntries={['/scans/scan1']}>
          <Routes>
            <Route path="/scans/:id" element={<ScanStatusPage />} />
          </Routes>
        </MemoryRouter>
      );
    });

    expect(api.scans.get).toHaveBeenCalledTimes(1);

    await act(async () => {
      vi.advanceTimersByTime(10000);
    });

    expect(api.scans.get).toHaveBeenCalledTimes(1);
  });
});
