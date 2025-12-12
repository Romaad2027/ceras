import React from 'react';
import { cn } from '../../lib/utils';

export const Input = React.forwardRef(
  (
    {
      id,
      label,
      className,
      error,
      type = 'text',
      hint,
      ...props
    },
    ref
  ) => {
    const inputId = id || React.useId();
    return (
      <div className={cn('w-full', className)}>
        {label && (
          <label
            htmlFor={inputId}
            className="mb-1 block text-sm font-medium text-surface-foreground"
          >
            {label}
          </label>
        )}
        <input
          id={inputId}
          ref={ref}
          type={type}
          className={cn(
            'w-full rounded-lg bg-surface-variant text-surface-foreground placeholder-[var(--md-sys-color-on-surface-variant)]',
            'border border-transparent focus:border-primary focus:ring-2 focus:ring-outline-variant focus:outline-none',
            'px-3 py-2 transition-shadow'
          )}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
          {...props}
        />
        {hint && !error && (
          <p id={`${inputId}-hint`} className="mt-1 text-xs text-[var(--md-sys-color-on-surface-variant)]">
            {hint}
          </p>
        )}
        {error && (
          <p id={`${inputId}-error`} className="mt-1 text-xs text-rose-400">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';


