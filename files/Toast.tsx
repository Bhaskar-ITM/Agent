import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { CheckCircle, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';

type ToastVariant = 'success' | 'error' | 'info' | 'warning';

interface ToastItem {
  id: string;
  variant: ToastVariant;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastContextType {
  toast: (options: Omit<ToastItem, 'id'>) => void;
  success: (title: string, message?: string) => void;
  error: (title: string, message?: string) => void;
  info: (title: string, message?: string) => void;
  warning: (title: string, message?: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

const VARIANT_CONFIG = {
  success: {
    icon: CheckCircle,
    border: 'border-l-emerald-500',
    iconColor: 'text-emerald-500',
    progressColor: 'bg-emerald-500',
  },
  error: {
    icon: AlertCircle,
    border: 'border-l-red-500',
    iconColor: 'text-red-500',
    progressColor: 'bg-red-500',
  },
  info: {
    icon: Info,
    border: 'border-l-blue-500',
    iconColor: 'text-blue-500',
    progressColor: 'bg-blue-500',
  },
  warning: {
    icon: AlertTriangle,
    border: 'border-l-amber-500',
    iconColor: 'text-amber-500',
    progressColor: 'bg-amber-500',
  },
};

function SingleToast({
  toast,
  onDismiss,
}: {
  toast: ToastItem;
  onDismiss: (id: string) => void;
}) {
  const [visible, setVisible] = useState(false);
  const [progress, setProgress] = useState(100);
  const duration = toast.duration ?? 4000;
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const dismiss = useCallback(() => {
    setVisible(false);
    setTimeout(() => onDismiss(toast.id), 300);
  }, [toast.id, onDismiss]);

  useEffect(() => {
    const showTimer = setTimeout(() => setVisible(true), 10);
    const dismissTimer = setTimeout(dismiss, duration);

    // Progress bar countdown
    const step = 50;
    intervalRef.current = setInterval(() => {
      setProgress(p => Math.max(0, p - (step / duration) * 100));
    }, step);

    return () => {
      clearTimeout(showTimer);
      clearTimeout(dismissTimer);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [dismiss, duration]);

  const config = VARIANT_CONFIG[toast.variant];
  const Icon = config.icon;

  return (
    <div
      className={`
        relative overflow-hidden flex items-start gap-3 p-4 rounded-xl
        shadow-lg shadow-slate-900/10 border border-slate-200 border-l-4
        bg-white min-w-[320px] max-w-[420px]
        transition-all duration-300 ease-out
        ${config.border}
        ${visible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-8'}
      `}
    >
      <Icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${config.iconColor}`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-slate-900 leading-snug">{toast.title}</p>
        {toast.message && (
          <p className="text-sm text-slate-500 mt-0.5 leading-snug">{toast.message}</p>
        )}
      </div>
      <button
        onClick={dismiss}
        className="text-slate-400 hover:text-slate-600 flex-shrink-0 p-0.5 rounded-md hover:bg-slate-100 transition-colors"
        aria-label="Dismiss notification"
      >
        <X className="w-3.5 h-3.5" />
      </button>
      {/* Progress bar */}
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-slate-100">
        <div
          className={`h-full transition-all ease-linear ${config.progressColor}`}
          style={{ width: `${progress}%`, transitionDuration: '50ms' }}
        />
      </div>
    </div>
  );
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const addToast = useCallback((options: Omit<ToastItem, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    setToasts(prev => [...prev.slice(-4), { ...options, id }]);
  }, []);

  const value: ToastContextType = {
    toast: addToast,
    success: (title, message) => addToast({ variant: 'success', title, message }),
    error: (title, message) => addToast({ variant: 'error', title, message }),
    info: (title, message) => addToast({ variant: 'info', title, message }),
    warning: (title, message) => addToast({ variant: 'warning', title, message }),
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        role="region"
        aria-label="Notifications"
        aria-live="polite"
        className="fixed bottom-6 right-6 z-[200] flex flex-col gap-2.5 pointer-events-none"
      >
        {toasts.map(t => (
          <div key={t.id} className="pointer-events-auto">
            <SingleToast toast={t} onDismiss={dismiss} />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextType {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within a ToastProvider');
  return context;
}
