import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ScanStatusPage from './ScanStatusPage';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: {
    scans: {
      get: vi.fn(),
      getResults: vi.fn(),
    }
  }
}));

describe('ScanStatusPage', () => {
  const mockScan = {
    scan_id: 'scan-123',
    project_id: 'proj-1',
    state: 'COMPLETED',
    started_at: '2023-01-01T10:00:00Z',
    finished_at: '2023-01-01T10:05:00Z',
    results: [
      { stage: 'git_checkout', status: 'PASS', summary: 'Checked out successfully' },
      { stage: 'nmap_scan', status: 'PASS', summary: 'No open ports found' }
    ]
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (api.scans.get as any).mockResolvedValue(mockScan);
  });

  it('renders human-readable stage names', async () => {
    render(
      <MemoryRouter initialEntries={['/scans/scan-123']}>
        <Routes>
          <Route path="/scans/:id" element={<ScanStatusPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByText('Scan Status')).toBeInTheDocument();

    // Check for human-readable names instead of internal IDs
    expect(screen.getByText('Git Checkout')).toBeInTheDocument();
    expect(screen.getByText('Nmap Scan')).toBeInTheDocument();

    // Verify internal IDs are NOT shown as the main title
    expect(screen.queryByText('git_checkout')).not.toBeInTheDocument();
  });

  it('shows last updated timestamp after loading', async () => {
    render(
      <MemoryRouter initialEntries={['/scans/scan-123']}>
        <Routes>
          <Route path="/scans/:id" element={<ScanStatusPage />} />
        </Routes>
      </MemoryRouter>
    );

    await screen.findByText('Scan Status');
    expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
  });

  it('copies scan ID to clipboard when copy button is clicked', async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText: writeTextMock,
      },
    });

    render(
      <MemoryRouter initialEntries={['/scans/scan-123']}>
        <Routes>
          <Route path="/scans/:id" element={<ScanStatusPage />} />
        </Routes>
      </MemoryRouter>
    );

    await screen.findByText('Scan Status');
    const copyBtn = screen.getByLabelText('Copy scan ID');
    fireEvent.click(copyBtn);

    expect(writeTextMock).toHaveBeenCalledWith('scan-123');

    // Check for success feedback (Check icon usually has aria-label or we can check for its presence if it changed)
    // In our case, it changes the icon. Let's wait for the Check icon's container or similar.
    // Or just check if the state change happened.
  });
});
