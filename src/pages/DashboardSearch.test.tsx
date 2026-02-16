import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DashboardPage from './DashboardPage';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: {
    projects: {
      list: vi.fn(),
    }
  }
}));

describe('DashboardPage Search', () => {
  const mockProjects = [
    { project_id: '1', name: 'Alpha Project', last_scan_state: 'COMPLETED' },
    { project_id: '2', name: 'Beta Project', last_scan_state: 'FAILED' },
    { project_id: '3', name: 'Gamma Project', last_scan_state: 'RUNNING' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (api.projects.list as any).mockResolvedValue(mockProjects);
  });

  it('filters projects based on search term', async () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    // Wait for projects to load
    expect(await screen.findByText('Alpha Project')).toBeInTheDocument();
    expect(screen.getByText('Beta Project')).toBeInTheDocument();
    expect(screen.getByText('Gamma Project')).toBeInTheDocument();

    const searchInput = screen.getByLabelText('Search projects');

    // Search for "Alpha"
    fireEvent.change(searchInput, { target: { value: 'Alpha' } });

    expect(screen.getByText('Alpha Project')).toBeInTheDocument();
    expect(screen.queryByText('Beta Project')).not.toBeInTheDocument();
    expect(screen.queryByText('Gamma Project')).not.toBeInTheDocument();
  });

  it('shows "No projects matching" message when no results found', async () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    await screen.findByText('Alpha Project');

    const searchInput = screen.getByLabelText('Search projects');

    // Search for something that doesn't exist
    fireEvent.change(searchInput, { target: { value: 'Zeta' } });

    expect(screen.queryByText('Alpha Project')).not.toBeInTheDocument();
    expect(screen.getByText(/No projects matching "Zeta"/)).toBeInTheDocument();
  });

  it('clears search when "Clear search" button is clicked', async () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    await screen.findByText('Alpha Project');

    const searchInput = screen.getByLabelText('Search projects');

    // Search for "Alpha"
    fireEvent.change(searchInput, { target: { value: 'Alpha' } });
    expect(screen.queryByText('Beta Project')).not.toBeInTheDocument();

    // Click clear button
    const clearButton = screen.getByLabelText('Clear search');
    fireEvent.click(clearButton);

    expect(searchInput).toHaveValue('');
    expect(screen.getByText('Alpha Project')).toBeInTheDocument();
    expect(screen.getByText('Beta Project')).toBeInTheDocument();
    expect(screen.getByText('Gamma Project')).toBeInTheDocument();
  });
});
