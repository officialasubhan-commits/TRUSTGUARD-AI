import React from 'react';
import { cn } from '../../utils/cn';

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'rectangle' | 'circle' | 'card';
  width?: string | number;
  height?: string | number;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className,
  variant = 'text',
  width,
  height,
  style,
  ...props
}) => {
  const variants = {
    text: 'h-3.5 w-full bg-[#181818] rounded-none',
    rectangle: 'h-24 w-full bg-[#141414] border border-[#292929]',
    circle: 'w-10 h-10 bg-[#181818] rounded-full border border-[#292929]',
    card: 'h-36 w-full bg-[#141414] border border-[#292929] p-4',
  };

  return (
    <div
      aria-hidden="true"
      className={cn('animate-pulse', variants[variant], className)}
      style={{
        width,
        height,
        ...style,
      }}
      {...props}
    />
  );
};

