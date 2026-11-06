import React from 'react';
import { Loader2, AlertTriangle, Inbox, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export const LoadingState: React.FC<{
  message?: string;
  className?: string;
}> = ({ message = 'Loading investigation data...', className = '' }) => {
  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center text-zinc-400 gap-3 ${className}`}>
      <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
      <p className="text-xs font-mono">{message}</p>
    </div>
  );
};

export const ErrorState: React.FC<{
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}> = ({
  title = 'Failed to load data',
  message = 'The backend service was unreachable or returned an error.',
  onRetry,
  className = '',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center text-zinc-300 gap-3 bg-rose-950/20 border border-rose-900/40 rounded-lg ${className}`}>
      <div className="w-10 h-10 rounded-full bg-rose-950/80 border border-rose-800 flex items-center justify-center text-rose-400">
        <AlertTriangle className="w-5 h-5" />
      </div>
      <div>
        <h4 className="text-sm font-semibold text-rose-200">{title}</h4>
        <p className="text-xs text-zinc-400 mt-1 max-w-md">{message}</p>
      </div>
      {onRetry && (
        <Button variant="secondary" size="sm" icon={<RefreshCw className="w-3.5 h-3.5" />} onClick={onRetry}>
          Retry Request
        </Button>
      )}
    </div>
  );
};

export const EmptyState: React.FC<{
  title: string;
  description: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}> = ({ title, description, action, icon, className = '' }) => {
  return (
    <div className={`flex flex-col items-center justify-center p-12 text-center text-zinc-400 gap-3 border border-dashed border-zinc-800 rounded-lg ${className}`}>
      <div className="w-10 h-10 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-500">
        {icon || <Inbox className="w-5 h-5" />}
      </div>
      <div>
        <h4 className="text-sm font-medium text-zinc-200">{title}</h4>
        <p className="text-xs text-zinc-500 mt-1 max-w-md">{description}</p>
      </div>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
};
