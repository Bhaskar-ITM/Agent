import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Eye, EyeOff } from 'lucide-react';

const LoginPage = () => {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mb-4">
            <Shield className="w-10 h-10 text-white" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Security Platform</h1>
          <p className="text-slate-500">Sign in to manage your scans</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1">
              Email <span className="text-red-500 ml-1" aria-hidden="true">*</span>
            </label>
            <input
              id="email"
              type="email"
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
              placeholder="admin@example.com"
              required
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-1">Password</label>
            <div className="relative group">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                className="w-full pl-4 pr-11 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
                placeholder="••••••••"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none focus:text-blue-600 transition-colors p-1 rounded-md"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg transition-colors mt-6 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 outline-none"
          >
            Sign In
          </button>
        </form>

        <div className="mt-8 text-center text-xs text-slate-400">
          PRODUCTION GRADE DEVSECOPS PLATFORM
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
