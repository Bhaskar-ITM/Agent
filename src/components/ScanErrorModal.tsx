import { X, ExternalLink, Copy, AlertTriangle } from 'lucide-react';
import { useState } from 'react';

interface ScanErrorModalProps {
  isOpen: boolean;
  onClose: () => void;
  error: {
    message: string;
    error_type?: string;
    jenkins_console_url?: string;
  } | null;
}

export function ScanErrorModal({ isOpen, onClose, error }: ScanErrorModalProps) {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !error) return null;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(error.message);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getErrorIcon = () => {
    switch (error.error_type) {
      case 'PIPELINE_ERROR':
      case 'TIMEOUT':
        return <AlertTriangle className="w-6 h-6 text-amber-500" />;
      case 'USER_CANCELLED':
        return <X className="w-6 h-6 text-blue-500" />;
      default:
        return <AlertTriangle className="w-6 h-6 text-red-500" />;
    }
  };

  const getErrorTitle = () => {
    switch (error.error_type) {
      case 'PIPELINE_ERROR':
        return 'Pipeline Error';
      case 'TIMEOUT':
        return 'Scan Timeout';
      case 'USER_CANCELLED':
        return 'Cancelled by User';
      case 'ADMIN_RECOVERY':
        return 'Admin Recovery';
      default:
        return 'Scan Failed';
    }
  };

  const getSuggestion = () => {
    switch (error.error_type) {
      case 'PIPELINE_ERROR':
        return 'Check the Jenkins console for syntax errors in the Jenkinsfile. Update the pipeline and try again.';
      case 'TIMEOUT':
        return 'The scan took too long to complete. Consider increasing the timeout or check for stuck stages.';
      case 'USER_CANCELLED':
        return 'Scan was manually cancelled. You can retry the scan if needed.';
      default:
        return 'Review the error details and try again.';
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div 
        className="bg-white rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-auto shadow-2xl animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
              {getErrorIcon()}
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-900">{getErrorTitle()}</h3>
              <p className="text-sm text-slate-500">Scan Error Details</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Error Message */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-slate-700">Error Message</label>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 transition-colors"
              >
                {copied ? (
                  <>
                    <X className="w-3 h-3" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    Copy
                  </>
                )}
              </button>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <pre className="text-sm text-slate-800 whitespace-pre-wrap font-mono">
                {error.message}
              </pre>
            </div>
          </div>

          {/* Jenkins Console Link */}
          {error.jenkins_console_url && (
            <div>
              <label className="text-sm font-medium text-slate-700 mb-2 block">Jenkins Console</label>
              <a
                href={error.jenkins_console_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                View Jenkins Console Output
              </a>
            </div>
          )}

          {/* Suggestion */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-blue-900 mb-1">Suggested Fix</h4>
                <p className="text-sm text-blue-800">{getSuggestion()}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-slate-200 bg-slate-50 rounded-b-2xl">
          <button
            onClick={onClose}
            className="px-4 py-2 text-slate-700 font-medium hover:bg-slate-200 rounded-lg transition-colors"
          >
            Close
          </button>
          {error.jenkins_console_url && (
            <a
              href={error.jenkins_console_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <ExternalLink className="w-4 h-4" />
              Open Jenkins Console
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
