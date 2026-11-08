import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string;
  error?: string;
  hint?: string;
  leftElement?: React.ReactNode;
  rightElement?: React.ReactNode;
  mono?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      label,
      error,
      hint,
      type = 'text',
      size = 'md',
      leftElement,
      rightElement,
      mono = false,
      disabled,
      ...props
    },
    ref
  ) => {
    const [showPassword, setShowPassword] = useState(false);
    const isPassword = type === 'password';
    const computedType = isPassword ? (showPassword ? 'text' : 'password') : type;

    const sizes = {
      sm: 'h-8 px-2.5 text-xs',
      md: 'h-10 px-3 text-xs',
      lg: 'h-12 px-4 text-sm',
    };

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label className="block text-xs font-mono text-[#A1A1A1] uppercase tracking-wider">
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {leftElement && (
            <div className="absolute left-3 flex items-center pointer-events-none text-[#666666]">
              {leftElement}
            </div>
          )}
          <input
            ref={ref}
            type={computedType}
            disabled={disabled}
            className={cn(
              'w-full bg-[#101010] border border-[#292929] text-[#F5F5F5] placeholder-[#666666] transition-colors focus-ring disabled:opacity-40 disabled:cursor-not-allowed',
              sizes[size],
              mono ? 'font-mono' : 'font-sans',
              leftElement && 'pl-9',
              (rightElement || isPassword) && 'pr-9',
              error ? 'border-[#F87171] focus:border-[#F87171]' : 'focus:border-[#F5F5F5]',
              className
            )}
            {...props}
          />
          {isPassword && !rightElement && (
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              tabIndex={-1}
              className="absolute right-3 flex items-center text-[#666666] hover:text-[#F5F5F5] transition-colors"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          )}
          {rightElement && (
            <div className="absolute right-3 flex items-center text-[#666666]">
              {rightElement}
            </div>
          )}
        </div>
        {error && <p className="text-xs font-mono text-[#F87171] tracking-wide">{error}</p>}
        {hint && !error && <p className="text-xs text-[#666666] tracking-wide">{hint}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
