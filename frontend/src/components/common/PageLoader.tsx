import React from 'react';

export interface PageLoaderProps {
  message?: string;
}

export const PageLoader: React.FC<PageLoaderProps> = ({ message = 'INITIALIZING SYSTEM...' }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
      <div className="relative w-8 h-8">
        <div className="absolute inset-0 border border-[#292929]" />
        <div className="absolute inset-1 border border-t-[#F5F5F5] border-r-transparent border-b-transparent border-l-transparent animate-spin" />
        <div className="absolute inset-3 bg-[#F5F5F5] animate-pulse" />
      </div>
      <p className="text-xs font-mono tracking-widest text-[#A1A1A1] uppercase">{message}</p>
    </div>
  );
};

