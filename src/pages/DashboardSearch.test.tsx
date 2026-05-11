import { render, screen, fireEvent, act } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import DashboardPage from "./DashboardPage";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { api } from "../services/api";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ToastProvider } from "../components/Toast";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

vi.mock("../services/api", () => ({
  api: {
    projects: {
      list: vi.fn(),
    },
    reports: {
      getSummary: vi.fn(),
    },
  },
  // Mock ApiError if used by components during render
  ApiError: {
    fromAxiosError: vi.fn(),
    isApiError: vi.fn().mockReturnValue(false),
  }
}));

// Mock useScanWebSocket to avoid infinite loops with fake timers
vi.mock("../hooks/useScanWebSocket", () => ({
  useScanWebSocket: vi.fn().mockReturnValue({ connected: true }),
}));

describe("DashboardPage Search", () => {
  const mockProjects = [
    { project_id: "1", name: "Alpha Project", last_scan_state: "COMPLETED" },
    { project_id: "2", name: "Beta Project", last_scan_state: "FAILED" },
    { project_id: "3", name: "Gamma Project", last_scan_state: "RUNNING" },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    (api.projects.list as any).mockResolvedValue(mockProjects);
    (api.reports.getSummary as any).mockResolvedValue({
      total_findings: 0,
      severity: { critical: 0, high: 0, medium: 0, low: 0, info: 0 }
    });
    queryClient.clear();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  const waitForLoad = async () => {
    // Initial load of projects
    await act(async () => {
      await Promise.resolve();
    });

    // Advance timers for TanStack Query to transition states
    await act(async () => {
      vi.advanceTimersByTime(100);
    });

    // Need more ticks for the enabled report-summaries query
    await act(async () => {
      await Promise.resolve();
      vi.advanceTimersByTime(100);
    });

    await act(async () => {
      await Promise.resolve();
    });
  };

  it("filters projects based on search term after debounce", async () => {
    render(
      <ToastProvider>
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <DashboardPage />
          </MemoryRouter>
        </QueryClientProvider>
      </ToastProvider>,
    );

    await waitForLoad();

    expect(screen.getByText("Alpha Project")).toBeInTheDocument();
    expect(screen.getByText("Beta Project")).toBeInTheDocument();
    expect(screen.getByText("Gamma Project")).toBeInTheDocument();

    const searchInput = screen.getByLabelText("Search projects");

    // Search for "Alpha"
    fireEvent.change(searchInput, { target: { value: "Alpha" } });

    // Advance timers for debounce (300ms)
    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(screen.queryByText("Alpha Project")).toBeInTheDocument();
    expect(screen.queryByText("Beta Project")).not.toBeInTheDocument();
    expect(screen.queryByText("Gamma Project")).not.toBeInTheDocument();
  });

  it('shows "No projects found" message after debounce', async () => {
    render(
      <ToastProvider>
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <DashboardPage />
          </MemoryRouter>
        </QueryClientProvider>
      </ToastProvider>,
    );

    await waitForLoad();

    const searchInput = screen.getByLabelText("Search projects");

    // Search for something that doesn't exist
    fireEvent.change(searchInput, { target: { value: "Zeta" } });

    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(screen.queryByText("Alpha Project")).not.toBeInTheDocument();
    expect(screen.getByText("No projects found")).toBeInTheDocument();
    expect(
      screen.getByText(/No projects matching "Zeta"/),
    ).toBeInTheDocument();
  });

  it('clears search when "Clear search" button is clicked', async () => {
    render(
      <ToastProvider>
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <DashboardPage />
          </MemoryRouter>
        </QueryClientProvider>
      </ToastProvider>,
    );

    await waitForLoad();

    const searchInput = screen.getByLabelText("Search projects");

    // Search for "Alpha"
    fireEvent.change(searchInput, { target: { value: "Alpha" } });

    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(screen.queryByText("Beta Project")).not.toBeInTheDocument();

    // Click clear button
    const clearButton = screen.getByLabelText("Clear search");
    fireEvent.click(clearButton);

    // Search term clears immediately
    expect(searchInput).toHaveValue("");

    // List also reverts after its own debounce
    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(screen.getByText("Alpha Project")).toBeInTheDocument();
    expect(screen.getByText("Beta Project")).toBeInTheDocument();
    expect(screen.getByText("Gamma Project")).toBeInTheDocument();
  });
});
