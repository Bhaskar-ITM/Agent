import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Save, ChevronLeft, Globe, GitBranch, Lock, ShieldCheck, MapPin, Link as LinkIcon } from 'lucide-react';

const CreateProjectPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    gitUrl: '',
    branch: 'main',
    credentials: '',
    sonarKey: '',
    targetIp: '',
    targetUrl: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.projects.create(formData);
      navigate('/dashboard');
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  return (
    <div className="max-w-3xl mx-auto">
      <button
        onClick={() => navigate('/dashboard')}
        className="flex items-center gap-2 text-slate-500 hover:text-slate-800 mb-6 transition-colors"
      >
        <ChevronLeft className="w-4 h-4" />
        Back to Dashboard
      </button>

      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-8 border-b border-slate-100 bg-slate-50">
          <h2 className="text-xl font-bold text-slate-900">Project Configuration</h2>
          <p className="text-slate-500 text-sm mt-1">Set up your project details. You can trigger scans after creation.</p>
        </div>

        <form onSubmit={handleSubmit} className="p-8 space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Project Name */}
            <div className="col-span-2">
              <label htmlFor="project-name" className="block text-sm font-semibold text-slate-700 mb-2">Project Name</label>
              <div className="relative">
                <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  id="project-name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="My Secure App"
                  className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                  required
                />
              </div>
            </div>

            {/* Git URL */}
            <div className="col-span-2">
              <label htmlFor="git-url" className="block text-sm font-semibold text-slate-700 mb-2">Git Repository URL</label>
              <div className="relative">
                <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  id="git-url"
                  name="gitUrl"
                  value={formData.gitUrl}
                  onChange={handleChange}
                  placeholder="https://github.com/org/repo.git"
                  className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                  required
                />
              </div>
            </div>

            {/* Branch */}
            <div>
              <label htmlFor="branch" className="block text-sm font-semibold text-slate-700 mb-2">Branch</label>
              <div className="relative">
                <GitBranch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  id="branch"
                  name="branch"
                  value={formData.branch}
                  onChange={handleChange}
                  placeholder="main"
                  className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                  required
                />
              </div>
            </div>

            {/* Credentials */}
            <div>
              <label htmlFor="credentials" className="block text-sm font-semibold text-slate-700 mb-2">Git Credentials (ID)</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  id="credentials"
                  name="credentials"
                  value={formData.credentials}
                  onChange={handleChange}
                  placeholder="git-cred-uuid"
                  className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                  required
                />
              </div>
            </div>

            {/* Sonar Key */}
            <div className="col-span-2">
              <label htmlFor="sonar-key" className="block text-sm font-semibold text-slate-700 mb-2">Sonar Project Key</label>
              <div className="relative">
                <ShieldCheck className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  id="sonar-key"
                  name="sonarKey"
                  value={formData.sonarKey}
                  onChange={handleChange}
                  placeholder="project-unique-key"
                  className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                  required
                />
              </div>
            </div>

            <div className="col-span-2 pt-4 border-t border-slate-100">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4">Target Information (Optional)</h3>
            </div>

            {/* Target IP */}
            <div>
              <label htmlFor="target-ip" className="block text-sm font-semibold text-slate-700 mb-2">Target IP (for Nmap)</label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  id="target-ip"
                  name="targetIp"
                  value={formData.targetIp}
                  onChange={handleChange}
                  placeholder="192.168.1.1"
                  className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                />
              </div>
            </div>

            {/* Target URL */}
            <div>
              <label htmlFor="target-url" className="block text-sm font-semibold text-slate-700 mb-2">Target URL (for ZAP)</label>
              <div className="relative">
                <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  id="target-url"
                  name="targetUrl"
                  value={formData.targetUrl}
                  onChange={handleChange}
                  placeholder="https://app.example.com"
                  className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-6 border-t border-slate-100">
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="px-6 py-2 border border-slate-200 text-slate-600 rounded-lg hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-2 rounded-lg font-semibold flex items-center gap-2 transition-colors disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {loading ? 'Creating...' : 'Create Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateProjectPage;
