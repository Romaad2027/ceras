import React from 'react';
import { cn } from '../../lib/utils';

const variantClasses = {
  primary:
    'bg-primary text-primary-foreground hover:brightness-95 shadow-md',
  secondary:
    'bg-surface text-primary border border-outline hover:bg-secondary-container',
  danger:
    'bg-error-container text-[var(--md-sys-color-on-error-container)] border border-outline-variant hover:brightness-95',
  ghost:
    'text-surface-foreground hover:bg-secondary-container',
};

const sizeClasses = {
  sm: 'h-8 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
  lg: 'h-12 px-5 text-base',
};

export const Button = React.forwardRef(
  ({ className, variant = 'primary', size = 'md', isLoading = false, icon, children, disabled, ...props }, ref) => {
    const isDisabled = disabled || isLoading;
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center rounded-lg font-medium transition-colors outline-none',
          'text-center select-none',
          'disabled:opacity-60 disabled:cursor-not-allowed',
          variantClasses[variant] || variantClasses.primary,
          sizeClasses[size] || sizeClasses.md,
          className
        )}
        disabled={isDisabled}
        aria-busy={isLoading}
        aria-disabled={isDisabled}
        {...props}
      >
        {isLoading ? (
          <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-[var(--md-sys-color-outline-variant)] border-t-transparent" />
        ) : (
          icon && <span className="mr-2 inline-flex items-center">{icon}</span>
        )}
        <span className="whitespace-nowrap">{children}</span>
      </button>
    );
  }
);

Button.displayName = 'Button';


