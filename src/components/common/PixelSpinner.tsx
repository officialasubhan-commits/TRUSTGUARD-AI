import React from 'react';

export interface PixelSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | number;
  className?: string;
}

export const PixelSpinner: React.FC<PixelSpinnerProps> = ({ size = 'md', className = '' }) => {
  const sizeClasses: Record<string, string> = {
    sm: 'w-5 h-5',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  const isNumeric = typeof size === 'number';
  const customStyle = isNumeric ? { width: `${size}px`, height: `${size}px` } : undefined;
  const dimensionClass = isNumeric ? '' : sizeClasses[size as string] || 'w-8 h-8';

  return (
    <div
      style={customStyle}
      className={`relative inline-block ${dimensionClass} ${className}`}
    >
      <div className="absolute inset-0 border border-[#2a2a2a]" />
      <div className="absolute inset-1 border border-t-white border-r-transparent border-b-transparent border-l-transparent animate-spin" />
      <div className="absolute inset-2 bg-white/40 animate-pulse" />
    </div>
  );
};
