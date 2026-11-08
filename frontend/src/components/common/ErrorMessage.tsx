import React from 'react';
import { AlertCircle } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface ErrorMessageProps {
  title?: string;
  message: string;
  code?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title = 'SECURITY BOUNDARY WARNING',
  message,
  code,
  onRetry,
  className,
}) => {
  return (
    <div
      className={cn(
        'border border-[#292929] bg-[#141414] p-4 text-xs font-mono space-y-2',
        className
      )}
    >
      <div className="flex items-center space-x-2 text-[#F5F5F5]">
        <AlertCircle className="w-4 h-4 shrink-0" />
        <span className="font-semibold tracking-wide uppercase">{title}</span>
        {code && <span className="text-[#666666]">[{code}]</span>}
      </div>
      <p className="text-[#A1A1A1] pl-6 font-sans text-sm">{message}</p>
      {onRetry && (
        <div className="pl-6 pt-1">
          <button
            onClick={onRetry}
            className="text-xs font-mono text-[#F5F5F5] underline hover:text-white transition-colors"
          >
            [RETRY OPERATION]
          </button>
        </div>
      )}
    </div>
  );
};

