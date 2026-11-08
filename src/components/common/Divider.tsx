import React from 'react';
import { cn } from '../../utils/cn';

export interface DividerProps extends React.HTMLAttributes<HTMLDivElement> {
  label?: string;
  orientation?: 'horizontal' | 'vertical';
  align?: 'left' | 'center' | 'right';
}

export const Divider: React.FC<DividerProps> = ({
  className,
  label,
  orientation = 'horizontal',
  align = 'center',
  ...props
}) => {
  if (orientation === 'vertical') {
    return <div className={cn('w-[1px] h-full bg-[#292929]', className)} {...props} />;
  }

  if (!label) {
    return <hr className={cn('w-full border-t border-[#292929] my-4', className)} {...props} />;
  }

  const aligns = {
    left: 'justify-start',
    center: 'justify-center',
    right: 'justify-end',
  };

  return (
    <div className={cn('relative flex items-center my-6', aligns[align], className)} {...props}>
      <div className="absolute inset-0 flex items-center">
        <div className="w-full border-t border-[#292929]" />
      </div>
      <div className="relative bg-[#080808] px-3">
        <span className="text-[11px] font-mono tracking-widest text-[#666666] uppercase">
          {label}
        </span>
      </div>
    </div>
  );
};

