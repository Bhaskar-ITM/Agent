import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ScanStatusPage from './ScanStatusPage';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: {
    scans: {
      get: vi.fn(),
    },
    projects: {
      get: vi.fn(),
    }
  }
}));

describe('ScanStatusPage Progress Bar', () => {
  const mockScan = {
    scan_id: 'scan-1',
    project_id: 'proj-1',
    state: 'RUNNING',
    started_at: '2025-01-01T00:00:00Z',
    results: [
      { stage: 'Git Checkout', status: 'PASS' },
      { stage: 'Sonar Scanner', status: 'RUNNING' },
      { stage: 'ZAP Scan', status: 'PENDING' },
    ]
  };

  const mockProject = {
    project_id: 'proj-1',
    name: 'Test Project'
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (api.scans.get as any).mockResolvedValue(mockScan); // eslint-disable-line @typescript-eslint/no-explicit-any
    (api.projects.get as any).mockResolvedValue(mockProject); // eslint-disable-line @typescript-eslint/no-explicit-any
  });

  it('calculates and displays the correct progress percentage', async () => {
    render(
      <MemoryRouter initialEntries={['/scans/scan-1']}>
        <Routes>
          <Route path="/scans/:id" element={<ScanStatusPage />} />
        </Routes>
      </MemoryRouter>
    );

    // Wait for the scan data to load
    expect(await screen.findByText('Overall Progress')).toBeInTheDocument();

    // 1 out of 3 stages are finished (PASS). 33%
    expect(screen.getByText('33%')).toBeInTheDocument();

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '33');
  });

  it('shows 100% when all stages are finished', async () => {
    const finishedScan = {
      ...mockScan,
      results: [
        { stage: 'Git Checkout', status: 'PASS' },
        { stage: 'Sonar Scanner', status: 'FAIL' },
        { stage: 'ZAP Scan', status: 'SKIPPED' },
      ]
    };
    (api.scans.get as any).mockResolvedValue(finishedScan); // eslint-disable-line @typescript-eslint/no-explicit-any

    render(
      <MemoryRouter initialEntries={['/scans/scan-1']}>
        <Routes>
          <Route path="/scans/:id" element={<ScanStatusPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByText('100%')).toBeInTheDocument();
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '100');
  });
});
