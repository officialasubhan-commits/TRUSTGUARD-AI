import React from 'react';
import { cn } from '../../utils/cn';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'standard' | 'elevated' | 'panel' | 'info';
  hoverEffect?: boolean;
  pixelFrame?: boolean;
  headerAction?: React.ReactNode;
  title?: string;
  subtitle?: string;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      className,
      variant = 'standard',
      hoverEffect = false,
      pixelFrame = false,
      headerAction,
      title,
      subtitle,
      children,
      ...props
    },
    ref
  ) => {
    const variants = {
      standard: 'bg-[#141414] border border-[#292929]',
      elevated: 'bg-[#181818] border border-[#383838] shadow-lg shadow-black/40',
      panel: 'bg-[#101010] border border-[#292929]',
      info: 'bg-[#141414] border border-[#292929] border-l-2 border-l-[#F5F5F5]',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'relative p-6 transition-colors duration-150',
          variants[variant],
          hoverEffect && 'hover:border-[#383838] hover:bg-[#1A1A1A]',
          className
        )}
        {...props}
      >
        {pixelFrame && (
          <>
            <span className="absolute top-0 left-0 w-1.5 h-1.5 bg-[#F5F5F5] -translate-x-0.5 -translate-y-0.5" />
            <span className="absolute top-0 right-0 w-1.5 h-1.5 bg-[#F5F5F5] translate-x-0.5 -translate-y-0.5" />
            <span className="absolute bottom-0 left-0 w-1.5 h-1.5 bg-[#F5F5F5] -translate-x-0.5 translate-y-0.5" />
            <span className="absolute bottom-0 right-0 w-1.5 h-1.5 bg-[#F5F5F5] translate-x-0.5 translate-y-0.5" />
          </>
        )}

        {(title || headerAction) && (
          <div className="flex items-start justify-between gap-4 mb-4 pb-3 border-b border-[#292929]">
            <div className="space-y-0.5">
              {title && (
                <h3 className="font-mono text-xs font-semibold uppercase tracking-wider text-[#F5F5F5]">
                  {title}
                </h3>
              )}
              {subtitle && <p className="text-xs text-[#A1A1A1]">{subtitle}</p>}
            </div>
            {headerAction && <div className="shrink-0">{headerAction}</div>}
          </div>
        )}

        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';
