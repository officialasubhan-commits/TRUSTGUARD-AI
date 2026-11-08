import React from 'react';
import { cn } from '../../utils/cn';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  pixelCorners?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      pixelCorners = false,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'relative inline-flex items-center justify-center font-mono tracking-wider transition-all duration-150 focus-ring disabled:opacity-40 disabled:cursor-not-allowed select-none uppercase font-medium';

    const variants = {
      primary:
        'bg-[#F5F5F5] text-[#080808] hover:bg-[#FFFFFF] active:bg-[#E5E5E5] border border-[#F5F5F5]',
      secondary:
        'bg-[#141414] text-[#F5F5F5] border border-[#292929] hover:border-[#383838] hover:bg-[#1A1A1A] active:bg-[#202020]',
      outline:
        'bg-transparent text-[#F5F5F5] border border-[#292929] hover:border-[#F5F5F5] hover:bg-[#101010]',
      ghost:
        'bg-transparent text-[#A1A1A1] hover:text-[#F5F5F5] hover:bg-[#141414] active:bg-[#1A1A1A] border border-transparent',
      danger:
        'bg-[#141414] text-[#F87171] border border-[#991B1B]/60 hover:border-[#F87171] hover:bg-[#450A0A]/40 active:bg-[#450A0A]/70',
    };

    const sizes = {
      sm: 'h-8 px-3 text-xs gap-1.5',
      md: 'h-10 px-4 text-xs gap-2',
      lg: 'h-12 px-6 text-sm gap-2.5',
      icon: 'h-10 w-10 p-0 text-sm',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        aria-busy={isLoading}
        className={cn(baseStyles, variants[variant], sizes[size], pixelCorners && 'pixel-corners', className)}
        {...props}
      >
        {isLoading ? (
          <span className="inline-block w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
        ) : (
          leftIcon
        )}
        {children && <span>{children}</span>}
        {!isLoading && rightIcon}
      </button>
    );
  }
);

Button.displayName = 'Button';
