import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ManualScanPage from './ManualScanPage';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: {
    projects: {
      get: vi.fn(),
    },
    scans: {
      trigger: vi.fn(),
    }
  },
  FIXED_STAGES: [
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
  ]
}));

describe('ManualScanPage', () => {
  const mockProject = {
    id: '1',
    name: 'Test Project',
    gitUrl: 'https://github.com/test/repo',
    branch: 'main',
    credentials: 'cred',
    sonarKey: 'sonar',
    targetIp: '1.2.3.4',
    targetUrl: 'https://test.com'
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.projects.get).mockResolvedValue(mockProject);
  });

  it('renders all 11 stages', async () => {
    render(
      <MemoryRouter initialEntries={['/projects/1/manual']}>
        <Routes>
          <Route path="/projects/:id/manual" element={<ManualScanPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByText('Git Checkout')).toBeInTheDocument();
    expect(screen.getByText('Sonar Scanner')).toBeInTheDocument();
    expect(screen.getByText('ZAP Scan')).toBeInTheDocument();
  });

  it('shows additional configuration when Nmap or ZAP is selected', async () => {
    render(
      <MemoryRouter initialEntries={['/projects/1/manual']}>
        <Routes>
          <Route path="/projects/:id/manual" element={<ManualScanPage />} />
        </Routes>
      </MemoryRouter>
    );

    await screen.findByText('Git Checkout');

    // Initially should not show "Additional Configuration Required"
    expect(screen.queryByText('Additional Configuration Required')).not.toBeInTheDocument();

    // Select Nmap Scan
    fireEvent.click(screen.getByText('Nmap Scan'));
    expect(screen.getByText('Additional Configuration Required')).toBeInTheDocument();
    expect(screen.getByText('Target IP (for Nmap)')).toBeInTheDocument();

    // Select ZAP Scan
    fireEvent.click(screen.getByText('ZAP Scan'));
    expect(screen.getByText('Target URL (for ZAP)')).toBeInTheDocument();
  });
});
