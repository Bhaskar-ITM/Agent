import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Loader2, AlertCircle, CheckCircle, Pencil } from 'lucide-react';
import { api } from '../services/api';
import { useToast } from '../components/Toast';

interface ProjectForm {
  name: string;
  git_url: string;
  branch: string;
  credentials_id: string;
  sonar_key: string;
  target_ip: string;
  target_url: string;
}

type FieldErrors = Partial<Record<keyof ProjectForm, string>>;

function validateField(name: keyof ProjectForm, value: string): string | null {
  if (name === 'name' && !value.trim()) return 'Project name is required.';
  if (name === 'git_url') {
    if (!value.trim()) return 'Git URL is required.';
    try { new URL(value); } catch { return 'Enter a valid URL (e.g. https://github.com/org/repo.git)'; }
  }
  if (name === 'sonar_key' && !value.trim()) return 'Sonar project key is required.';
  if (name === 'target_ip' && value.trim()) {
    const ipv4 = /^(\d{1,3}\.){3}\d{1,3}$/;
    const ipv6 = /^[0-9a-fA-F:]+$/;
    const host = /^[a-zA-Z0-9.-]+$/;
    if (!ipv4.test(value) && !ipv6.test(value) && !host.test(value)) {
      return 'Enter a valid IP address or hostname.';
    }
  }
  if (name === 'target_url' && value.trim()) {
    try { new URL(value); } catch { return 'Enter a valid URL (e.g. https://example.com)'; }
  }
  return null;
}

const FIELDS: {
  name: keyof ProjectForm;
  label: string;
  type?: string;
  placeholder: string;
  required?: boolean;
  hint?: string;
}[] = [
  { name: 'name', label: 'Project Name', placeholder: 'My Web Application', required: true },
  { name: 'git_url', label: 'Git Repository URL', type: 'url', placeholder: 'https://github.com/user/repo.git', required: true },
  { name: 'branch', label: 'Branch', placeholder: 'main' },
  { name: 'credentials_id', label: 'Credentials ID', placeholder: 'git-credentials' },
  { name: 'sonar_key', label: 'Sonar Project Key', placeholder: 'my-web-app', required: true },
  { name: 'target_ip', label: 'Target IP Address', placeholder: '192.168.1.100', hint: 'Required for Nmap scans' },
  { name: 'target_url', label: 'Target URL', type: 'url', placeholder: 'https://example.com', hint: 'Required for ZAP scans' },
];

const EditProjectPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { success, error: toastError } = useToast();

  const [form, setForm] = useState<ProjectForm>({
    name: '', git_url: '', branch: 'main',
    credentials_id: '', sonar_key: '', target_ip: '', target_url: '',
  });
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [touched, setTouched] = useState<Partial<Record<keyof ProjectForm, boolean>>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [originalName, setOriginalName] = useState('');

  useEffect(() => {
    if (!id) return;
    api.projects.get(id).then(data => {
      if (!data) { setFetchError('Project not found.'); setIsFetching(false); return; }
      const f: ProjectForm = {
        name: data.name || '',
        git_url: data.git_url || '',
        branch: data.branch || 'main',
        credentials_id: data.credentials_id || '',
        sonar_key: data.sonar_key || '',
        target_ip: data.target_ip || '',
        target_url: data.target_url || '',
      };
      setForm(f);
      setOriginalName(data.name || '');
    }).catch(() => {
      setFetchError('Failed to load project details.');
    }).finally(() => setIsFetching(false));
  }, [id]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
    if (touched[name as keyof ProjectForm]) {
      const err = validateField(name as keyof ProjectForm, value);
      setFieldErrors(prev => ({ ...prev, [name]: err || undefined }));
    }
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setTouched(prev => ({ ...prev, [name]: true }));
    const err = validateField(name as keyof ProjectForm, value);
    setFieldErrors(prev => ({ ...prev, [name]: err || undefined }));
  };

  const validateAll = (): boolean => {
    const errors: FieldErrors = {};
    let valid = true;
    FIELDS.forEach(f => {
      const err = validateField(f.name, form[f.name]);
      if (err) { errors[f.name] = err; valid = false; }
    });
    setFieldErrors(errors);
    setTouched(Object.fromEntries(FIELDS.map(f => [f.name, true])));
    return valid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateAll()) return;
    if (!id) return;

    setIsLoading(true);
    try {
      await api.projects.update(id, {
        name: form.name,
        git_url: form.git_url,
        branch: form.branch,
        credentials_id: form.credentials_id,
        sonar_key: form.sonar_key,
        target_ip: form.target_ip || undefined,
        target_url: form.target_url || undefined,
      });
      success('Project updated', `"${form.name}" has been saved successfully.`);
      navigate(`/projects/${id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update project. Please try again.';
      toastError('Update failed', msg);
    } finally {
      setIsLoading(false);
    }
  };

  if (isFetching) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-500">
          <Loader2 className="animate-spin w-5 h-5" />
          Loading project details…
        </div>
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="bg-white rounded-xl border border-red-200 p-8 text-center max-w-sm">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
          <p className="text-slate-700 font-medium mb-4">{fetchError}</p>
          <button onClick={() => navigate('/dashboard')} className="text-blue-600 hover:underline text-sm">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <button
          onClick={() => navigate(`/projects/${id}`)}
          className="flex items-center gap-2 text-slate-500 hover:text-slate-800 text-sm transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Project
        </button>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Page header */}
        <div className="px-8 py-6 border-b border-slate-100 flex items-center gap-4">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center flex-shrink-0">
            <Pencil className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">Edit Project</h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Updating <span className="font-medium text-slate-700">{originalName}</span>
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-8 space-y-8">
          {/* Repository section */}
          <section>
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-5">
              Repository
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {FIELDS.slice(0, 2).map(field => (
                <FieldInput
                  key={field.name}
                  field={field}
                  value={form[field.name]}
                  error={fieldErrors[field.name]}
                  touched={!!touched[field.name]}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  disabled={isLoading}
                  className={field.name === 'git_url' ? 'md:col-span-2' : ''}
                />
              ))}
              <FieldInput
                field={FIELDS[2]} // branch
                value={form.branch}
                error={fieldErrors.branch}
                touched={!!touched.branch}
                onChange={handleChange}
                onBlur={handleBlur}
                disabled={isLoading}
              />
              <FieldInput
                field={FIELDS[3]} // credentials_id
                value={form.credentials_id}
                error={fieldErrors.credentials_id}
                touched={!!touched.credentials_id}
                onChange={handleChange}
                onBlur={handleBlur}
                disabled={isLoading}
              />
            </div>
          </section>

          {/* Analysis section */}
          <section>
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-5">
              Code Analysis
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <FieldInput
                field={FIELDS[4]} // sonar_key
                value={form.sonar_key}
                error={fieldErrors.sonar_key}
                touched={!!touched.sonar_key}
                onChange={handleChange}
                onBlur={handleBlur}
                disabled={isLoading}
              />
            </div>
          </section>

          {/* Security targets section */}
          <section>
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-1">
              Security Scan Targets
            </h2>
            <p className="text-xs text-slate-400 mb-5">
              Optional — required only for Nmap and ZAP scan stages.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {FIELDS.slice(5).map(field => (
                <FieldInput
                  key={field.name}
                  field={field}
                  value={form[field.name]}
                  error={fieldErrors[field.name]}
                  touched={!!touched[field.name]}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  disabled={isLoading}
                />
              ))}
            </div>
          </section>

          {/* Actions */}
          <div className="flex items-center gap-3 pt-4 border-t border-slate-100">
            <button
              type="submit"
              disabled={isLoading}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-2.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              {isLoading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Saving…</>
              ) : (
                <><Save className="w-4 h-4" /> Save Changes</>
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate(`/projects/${id}`)}
              disabled={isLoading}
              className="px-6 py-2.5 border border-slate-200 text-slate-600 font-semibold rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50 text-sm"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Field input sub-component
function FieldInput({
  field, value, error, touched, onChange, onBlur, disabled, className = '',
}: {
  field: (typeof FIELDS)[number];
  value: string;
  error?: string;
  touched: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur: (e: React.FocusEvent<HTMLInputElement>) => void;
  disabled: boolean;
  className?: string;
}) {
  const isValid = touched && !error && value.trim();
  const isError = touched && !!error;

  return (
    <div className={className}>
      <label htmlFor={field.name} className="block text-sm font-medium text-slate-700 mb-1.5">
        {field.label}
        {field.required && <span className="text-red-500 ml-1">*</span>}
      </label>
      <div className="relative">
        <input
          id={field.name}
          name={field.name}
          type={field.type || 'text'}
          value={value}
          onChange={onChange}
          onBlur={onBlur}
          placeholder={field.placeholder}
          disabled={disabled}
          className={`
            w-full px-3 py-2.5 rounded-lg border text-sm outline-none transition-all
            disabled:bg-slate-50 disabled:text-slate-400
            ${isError
              ? 'border-red-300 focus:border-red-400 focus:ring-2 focus:ring-red-100 pr-9'
              : isValid
              ? 'border-emerald-300 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100 pr-9'
              : 'border-slate-300 focus:border-blue-400 focus:ring-2 focus:ring-blue-100'
            }
          `}
        />
        {isError && (
          <AlertCircle className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-red-500 pointer-events-none" />
        )}
        {isValid && (
          <CheckCircle className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-500 pointer-events-none" />
        )}
      </div>
      {isError && <p className="text-xs text-red-600 mt-1">{error}</p>}
      {field.hint && !isError && <p className="text-xs text-slate-400 mt-1">{field.hint}</p>}
    </div>
  );
}

export default EditProjectPage;
