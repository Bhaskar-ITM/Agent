import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, AlertCircle, CheckCircle } from 'lucide-react';
import { api } from '../services/api';

const CreateProjectPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    git_url: '',
    branch: 'main',
    credentials_id: '',
    sonar_key: '',
    target_ip: '',
    target_url: ''
  });
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    // Validate required fields
    if (!formData.name || !formData.git_url || !formData.credentials_id || !formData.sonar_key) {
      setError('Please fill in all required fields (Name, Git URL, Credentials ID, Sonar Key)');
      return;
    }

    // Validate Git URL format
    try {
      new URL(formData.git_url);
    } catch {
      setError('Please enter a valid Git URL (e.g., https://github.com/org/repo.git)');
      return;
    }

    setIsLoading(true);
    try {
      const project = await api.projects.create(formData);
      setSuccessMessage(`Project "${project.name}" created successfully!`);
      // Reset form
      setFormData({
        name: '',
        git_url: '',
        branch: 'main',
        credentials_id: '',
        sonar_key: '',
        target_ip: '',
        target_url: ''
      });
      // Redirect to project control page after 2 seconds
      setTimeout(() => {
        navigate(`/projects/${project.project_id}`);
      }, 2000);
    } catch (err: unknown) {
      console.error('Project creation failed', err);
      const errorMessage = err && typeof err === 'object' && 'response' in err
        ? (err.response as { data?: { detail?: string } })?.data?.detail
        : 'Project creation failed. Please try again.';
      setError(errorMessage || 'Project creation failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <Plus className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Create New Project</h1>
              <p className="text-slate-600">Set up a new project for security scanning</p>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              {error}
            </div>
          )}

          {successMessage && (
            <div className="bg-green-50 text-green-600 p-4 rounded-lg mb-6 flex items-center gap-3">
              <CheckCircle className="w-5 h-5 flex-shrink-0" />
              {successMessage}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-slate-700 mb-2">
                  Project Name <span className="text-red-500">*</span>
                </label>
                <input
                  id="name"
                  name="name"
                  type="text"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
                  placeholder="e.g., My Web Application"
                  required
                  disabled={isLoading}
                />
              </div>
              <div>
                <label htmlFor="git_url" className="block text-sm font-medium text-slate-700 mb-2">
                  Git Repository URL <span className="text-red-500">*</span>
                </label>
                <input
                  id="git_url"
                  name="git_url"
                  type="url"
                  value={formData.git_url}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
                  placeholder="https://github.com/user/repo.git"
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label htmlFor="branch" className="block text-sm font-medium text-slate-700 mb-2">
                  Branch
                </label>
                <input
                  id="branch"
                  name="branch"
                  type="text"
                  value={formData.branch}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
                  placeholder="main"
                  disabled={isLoading}
                />
              </div>
              <div>
                <label htmlFor="credentials_id" className="block text-sm font-medium text-slate-700 mb-2">
                  Credentials ID
                </label>
                <input
                  id="credentials_id"
                  name="credentials_id"
                  type="text"
                  value={formData.credentials_id}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
                  placeholder="git-credentials"
                  disabled={isLoading}
                />
              </div>
              <div>
                <label htmlFor="sonar_key" className="block text-sm font-medium text-slate-700 mb-2">
                  Sonar Project Key <span className="text-red-500">*</span>
                </label>
                <input
                  id="sonar_key"
                  name="sonar_key"
                  type="text"
                  value={formData.sonar_key}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
                  placeholder="my-web-app"
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="target_ip" className="block text-sm font-medium text-slate-700 mb-2">
                  Target IP Address
                </label>
                <input
                  id="target_ip"
                  name="target_ip"
                  type="text"
                  value={formData.target_ip}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
                  placeholder="192.168.1.100"
                  disabled={isLoading}
                />
              </div>
              <div>
                <label htmlFor="target_url" className="block text-sm font-medium text-slate-700 mb-2">
                  Target URL
                </label>
                <input
                  id="target_url"
                  name="target_url"
                  type="url"
                  value={formData.target_url}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
                  placeholder="https://example.com"
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="flex gap-4">
              <button
                type="submit"
                disabled={isLoading}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Creating Project...
                  </div>
                ) : (
                  "Create Project"
                )}
              </button>
              <button
                type="button"
                onClick={() => navigate('/dashboard')}
                className="border border-slate-300 text-slate-700 font-semibold px-6 py-3 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateProjectPage;