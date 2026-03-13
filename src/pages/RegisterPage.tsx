import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Eye, EyeOff, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import { api } from '../services/api';

const RegisterPage = () => {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await api.auth.register(username, password);
      navigate('/login', { 
        state: { message: 'Registration successful! Please sign in with your new credentials.' } 
      });
    } catch (err: unknown) {
      console.error('Registration failed', err);
      const errorMessage = err && typeof err === 'object' && 'response' in err 
        ? (err.response as { data?: { detail?: string } })?.data?.detail 
        : 'Initialization failed. Username might already be in use.';
      setError(errorMessage || 'Initialization failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute top-0 right-0 w-96 h-96 bg-blue-600/20 blur-[120px] rounded-full -translate-y-1/2 translate-x-1/2"></div>
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-blue-900/20 blur-[120px] rounded-full translate-y-1/2 -translate-x-1/2"></div>

      <div className="max-w-md w-full bg-white rounded-[2.5rem] shadow-2xl p-10 relative z-10 animate-in zoom-in-95 duration-500">
        <div className="flex flex-col items-center mb-10">
          <div className="w-20 h-20 bg-blue-600 rounded-[2rem] flex items-center justify-center mb-6 shadow-xl shadow-blue-900/20 ring-8 ring-blue-50">
            <Shield className="w-10 h-10 text-white" aria-hidden="true" />
          </div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight uppercase leading-none mb-2 text-center">Join the Pipeline</h1>
          <p className="text-slate-500 font-medium text-sm tracking-tight">Initialize your operator credentials</p>
        </div>

        <form onSubmit={handleRegister} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-100 text-red-600 p-4 rounded-2xl text-xs font-bold flex items-start gap-3 animate-shake">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              {error}
            </div>
          )}
          
          <div className="space-y-2">
            <label htmlFor="username" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">
              Choose Operator Name
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-field"
              placeholder="e.g. jdoe_sec"
              required
              autoFocus
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="block text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">
              Secure Access Token
            </label>
            <div className="relative group">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field pr-12"
                placeholder="Minimum 8 characters"
                required
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-300 hover:text-blue-600 transition-colors p-1 rounded-lg"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full btn-primary h-14 mt-4 flex items-center justify-center gap-3 uppercase tracking-widest text-xs"
          >
            {isLoading ? (
              <>
                <Loader2 className="animate-spin h-5 w-5" />
                Processing...
              </>
            ) : (
              <>
                <CheckCircle className="w-5 h-5" />
                Initialize Operator
              </>
            )}
          </button>
        </form>

        <div className="mt-10 text-center text-xs font-bold text-slate-400 uppercase tracking-widest">
          Already Enrolled?{' '}
          <Link to="/login" className="text-blue-600 hover:text-blue-700 transition-colors">
            Command Center Sign In
          </Link>
        </div>

        <div className="mt-12 pt-8 border-t border-slate-50 text-center text-[9px] font-black text-slate-300 uppercase tracking-[0.3em]">
          End-to-End Encryption Enabled
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
