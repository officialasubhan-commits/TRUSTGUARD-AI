import React from 'react';
import { cn } from '../../utils/cn';

export type SecurityStatusType = 'safe' | 'suspicious' | 'malicious' | 'unknown';

export interface StatusIndicatorProps {
  status: SecurityStatusType;
  label?: string;
  sublabel?: string;
  showDot?: boolean;
  pulse?: boolean;
  className?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  sublabel,
  showDot = true,
  pulse = false,
  className,
}) => {
  const configs: Record<
    SecurityStatusType,
    { dotColor: string; defaultLabel: string; symbol: string }
  > = {
    safe: {
      dotColor: 'bg-[#4ADE80]',
      defaultLabel: 'VERIFIED BENIGN',
      symbol: '[ ✓ ]',
    },
    suspicious: {
      dotColor: 'bg-[#FBBF24]',
      defaultLabel: 'SUSPICIOUS TELEMETRY',
      symbol: '[ ! ]',
    },
    malicious: {
      dotColor: 'bg-[#F87171]',
      defaultLabel: 'CONFIRMED THREAT',
      symbol: '[ ✕ ]',
    },
    unknown: {
      dotColor: 'bg-[#666666]',
      defaultLabel: 'STATUS UNKNOWN',
      symbol: '[ ? ]',
    },
  };

  const config = configs[status];

  return (
    <div className={cn('inline-flex items-center space-x-2 font-mono text-xs', className)}>
      {showDot && (
        <span className="relative flex h-2 w-2">
          {pulse && (
            <span
              className={cn(
                'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
                config.dotColor
              )}
            />
          )}
          <span className={cn('relative inline-flex rounded-full h-2 w-2', config.dotColor)} />
        </span>
      )}
      <div className="flex flex-col">
        <span className="text-[#F5F5F5] font-semibold tracking-wider uppercase">
          {label || config.defaultLabel}
        </span>
        {sublabel && <span className="text-[10px] text-[#666666] tracking-wide">{sublabel}</span>}
      </div>
    </div>
  );
};

