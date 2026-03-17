import { useEffect, useId } from 'react';
import { AlertTriangle, Trash2, RefreshCw, Info, X } from 'lucide-react';

type ConfirmVariant = 'danger' | 'warning' | 'info';

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string | React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: ConfirmVariant;
  isLoading?: boolean;
}

const VARIANT_CONFIG: Record<
  ConfirmVariant,
  { iconBg: string; iconColor: string; btnClass: string; Icon: React.ElementType }
> = {
  danger: {
    iconBg: 'bg-red-100',
    iconColor: 'text-red-600',
    btnClass: 'bg-red-600 hover:bg-red-700 focus:ring-red-500 text-white shadow-red-200',
    Icon: Trash2,
  },
  warning: {
    iconBg: 'bg-amber-100',
    iconColor: 'text-amber-600',
    btnClass: 'bg-amber-600 hover:bg-amber-700 focus:ring-amber-500 text-white shadow-amber-200',
    Icon: AlertTriangle,
  },
  info: {
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    btnClass: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500 text-white shadow-blue-200',
    Icon: Info,
  },
};

export function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger',
  isLoading = false,
}: ConfirmModalProps) {
  const titleId = useId();
  const { iconBg, iconColor, btnClass, Icon } = VARIANT_CONFIG[variant];

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isLoading) onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handler);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handler);
      document.body.style.overflow = '';
    };
  }, [isOpen, isLoading, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50"
      onClick={() => !isLoading && onClose()}
    >
      <div
        className="bg-white rounded-2xl max-w-md w-full p-8 shadow-2xl relative animate-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={e => e.stopPropagation()}
      >
        <button
          onClick={() => !isLoading && onClose()}
          disabled={isLoading}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-2 rounded-lg hover:bg-slate-100 transition-colors disabled:opacity-40"
          aria-label="Close"
        >
          <X className="w-4 h-4" />
        </button>

        <div className={`w-12 h-12 ${iconBg} rounded-full flex items-center justify-center mb-5`}>
          <Icon className={`w-6 h-6 ${iconColor}`} />
        </div>

        <h3 id={titleId} className="text-xl font-bold text-slate-900 mb-2">
          {title}
        </h3>
        <div className="text-slate-500 mb-8 leading-relaxed text-sm">{description}</div>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => !isLoading && onClose()}
            disabled={isLoading}
            className="flex-1 py-3 border border-slate-200 text-slate-600 rounded-xl hover:bg-slate-50 font-semibold transition-colors disabled:opacity-40 text-sm"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            className={`flex-1 py-3 rounded-xl font-semibold shadow-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2 text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 ${btnClass}`}
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Processing…
              </>
            ) : (
              confirmLabel
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
