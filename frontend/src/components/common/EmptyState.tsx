import React from 'react';
import { Database } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface EmptyStateProps {
  title?: string;
  description: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'NO RECORDS FOUND',
  description,
  action,
  icon,
  className,
}) => {
  return (
    <div
      className={cn(
        'border border-[#292929] bg-[#141414] p-12 text-center flex flex-col items-center justify-center space-y-4',
        className
      )}
    >
      <div className="w-12 h-12 rounded border border-[#292929] flex items-center justify-center text-[#666666]">
        {icon || <Database className="w-6 h-6" />}
      </div>
      <div className="space-y-1">
        <h3 className="text-sm font-mono uppercase tracking-wider text-[#F5F5F5]">{title}</h3>
        <p className="text-xs text-[#A1A1A1] max-w-sm">{description}</p>
      </div>
      {action && <div className="pt-2">{action}</div>}
    </div>
  );
};

