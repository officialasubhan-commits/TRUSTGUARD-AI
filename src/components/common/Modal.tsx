import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  footerActions?: React.ReactNode;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  footerActions,
  maxWidth = 'md',
}) => {
  const modalRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const maxWidths = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-[#080808]/80 backdrop-blur-sm transition-opacity"
      />

      {/* Modal Surface */}
      <div
        ref={modalRef}
        className={cn(
          'relative w-full bg-[#141414] border border-[#383838] shadow-2xl p-6 z-10 space-y-6',
          maxWidths[maxWidth]
        )}
      >
        {/* Pixel corners */}
        <span className="absolute top-0 left-0 w-1.5 h-1.5 bg-[#F5F5F5] -translate-x-0.5 -translate-y-0.5" />
        <span className="absolute top-0 right-0 w-1.5 h-1.5 bg-[#F5F5F5] translate-x-0.5 -translate-y-0.5" />
        <span className="absolute bottom-0 left-0 w-1.5 h-1.5 bg-[#F5F5F5] -translate-x-0.5 translate-y-0.5" />
        <span className="absolute bottom-0 right-0 w-1.5 h-1.5 bg-[#F5F5F5] translate-x-0.5 translate-y-0.5" />

        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-[#292929]">
          <div className="space-y-1">
            <h2 className="font-mono text-sm font-semibold tracking-wider text-[#F5F5F5] uppercase">
              {title}
            </h2>
            {subtitle && <p className="text-xs text-[#A1A1A1]">{subtitle}</p>}
          </div>
          <button
            onClick={onClose}
            className="text-[#666666] hover:text-[#F5F5F5] p-1 border border-transparent hover:border-[#292929] transition-colors"
            aria-label="Close dialog"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="text-sm text-[#A1A1A1]">{children}</div>

        {/* Footer */}
        {footerActions && (
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-[#292929]">
            {footerActions}
          </div>
        )}
      </div>
    </div>
  );
};

