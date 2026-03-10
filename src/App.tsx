import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Suspense, lazy } from 'react';
import { AuthProvider } from './hooks/useAuth';
import { ProtectedRoute } from './components/ProtectedRoute';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

// Code splitting: Lazy load page components
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const CreateProjectPage = lazy(() => import('./pages/CreateProjectPage'));
const ProjectControlPage = lazy(() => import('./pages/ProjectControlPage'));
const ManualScanPage = lazy(() => import('./pages/ManualScanPage'));
const ScanStatusPage = lazy(() => import('./pages/ScanStatusPage'));
const ScanHistoryPage = lazy(() => import('./pages/ScanHistoryPage'));

// Loading component for lazy-loaded routes
const PageLoader = () => (
  <div className="min-h-screen bg-slate-50 flex items-center justify-center">
    <div className="bg-white rounded-lg shadow-sm p-8 flex items-center gap-4">
      <svg className="animate-spin h-6 w-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span className="text-slate-700">Loading...</span>
    </div>
  </div>
);

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route
                path="/dashboard"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <DashboardPage />
                  </Suspense>
                }
              />
              <Route
                path="/projects/create"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <CreateProjectPage />
                  </Suspense>
                }
              />
              <Route
                path="/projects/:id"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <ProjectControlPage />
                  </Suspense>
                }
              />
              <Route
                path="/projects/:id/manual"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <ManualScanPage />
                  </Suspense>
                }
              />
              <Route
                path="/scans/:id"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <ScanStatusPage />
                  </Suspense>
                }
              />
              <Route
                path="/projects/:id/history"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <ScanHistoryPage />
                  </Suspense>
                }
              />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
