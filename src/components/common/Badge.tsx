import React from 'react';
import { cn } from '../../utils/cn';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?:
    | 'default'
    | 'inverted'
    | 'subtle'
    | 'outline'
    | 'safe'
    | 'suspicious'
    | 'malicious'
    | 'unknown';
  size?: 'xs' | 'sm' | 'md';
  dot?: boolean;
  pulse?: boolean;
  icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'default',
  size = 'sm',
  dot = false,
  pulse = false,
  icon,
  children,
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center font-mono font-medium tracking-wider uppercase select-none';

  const variants = {
    default: 'bg-[#181818] text-[#F5F5F5] border border-[#292929]',
    inverted: 'bg-[#F5F5F5] text-[#080808] border border-[#F5F5F5] font-semibold',
    subtle: 'bg-[#101010] text-[#A1A1A1] border border-[#222222]',
    outline: 'bg-transparent text-[#F5F5F5] border border-[#383838]',
    safe: 'bg-[#052E16] text-[#4ADE80] border border-[#166534]',
    suspicious: 'bg-[#451A03] text-[#FBBF24] border border-[#92400E]',
    malicious: 'bg-[#450A0A] text-[#F87171] border border-[#991B1B]',
    unknown: 'bg-[#141414] text-[#A1A1A1] border border-[#383838]',
  };

  const dotColors = {
    default: 'bg-[#F5F5F5]',
    inverted: 'bg-[#080808]',
    subtle: 'bg-[#A1A1A1]',
    outline: 'bg-[#F5F5F5]',
    safe: 'bg-[#4ADE80]',
    suspicious: 'bg-[#FBBF24]',
    malicious: 'bg-[#F87171]',
    unknown: 'bg-[#A1A1A1]',
  };

  const sizes = {
    xs: 'px-1.5 py-0.5 text-[10px] gap-1',
    sm: 'px-2.5 py-0.5 text-xs gap-1.5',
    md: 'px-3 py-1 text-xs gap-2',
  };

  return (
    <span className={cn(baseStyles, variants[variant], sizes[size], className)} {...props}>
      {dot && (
        <span
          className={cn(
            'inline-block w-1.5 h-1.5 rounded-full shrink-0',
            dotColors[variant],
            pulse && 'animate-pulse'
          )}
        />
      )}
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{children}</span>
    </span>
  );
};

