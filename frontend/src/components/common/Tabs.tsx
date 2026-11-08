import React from 'react';
import { cn } from '../../utils/cn';

export interface TabItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  count?: number;
}

export interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (tabId: string) => void;
  variant?: 'line' | 'pills';
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab,
  onChange,
  variant = 'line',
  className,
}) => {
  return (
    <div
      role="tablist"
      className={cn(
        'flex items-center space-x-1 border-b border-[#292929] text-xs font-mono',
        className
      )}
    >
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab;

        if (variant === 'pills') {
          return (
            <button
              key={tab.id}
              role="tab"
              aria-selected={isActive}
              onClick={() => onChange(tab.id)}
              className={cn(
                'inline-flex items-center space-x-2 px-3 py-1.5 transition-colors uppercase tracking-wider',
                isActive
                  ? 'bg-[#181818] text-[#F5F5F5] border border-[#383838]'
                  : 'text-[#A1A1A1] hover:text-[#F5F5F5] hover:bg-[#101010]'
              )}
            >
              {tab.icon && <span>{tab.icon}</span>}
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span className="text-[10px] px-1 bg-[#292929] text-[#A1A1A1] rounded">
                  {tab.count}
                </span>
              )}
            </button>
          );
        }

        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.id)}
            className={cn(
              'relative inline-flex items-center space-x-2 px-4 py-2.5 transition-colors uppercase tracking-wider',
              isActive ? 'text-[#F5F5F5]' : 'text-[#666666] hover:text-[#A1A1A1]'
            )}
          >
            {tab.icon && <span>{tab.icon}</span>}
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span className="text-[10px] text-[#666666]">({tab.count})</span>
            )}
            {isActive && (
              <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-[#F5F5F5]" />
            )}
          </button>
        );
      })}
    </div>
  );
};

