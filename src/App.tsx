import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import CreateProjectPage from './pages/CreateProjectPage';
import ProjectControlPage from './pages/ProjectControlPage';
import ManualScanPage from './pages/ManualScanPage';
import ScanStatusPage from './pages/ScanStatusPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/projects/create" element={<CreateProjectPage />} />
          <Route path="/projects/:id" element={<ProjectControlPage />} />
          <Route path="/projects/:id/manual" element={<ManualScanPage />} />
          <Route path="/scans/:id" element={<ScanStatusPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
