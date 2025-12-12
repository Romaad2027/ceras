import { cn } from '../../lib/utils';

const variantClasses = {
  success: 'bg-primary-container text-primary-container-foreground border-outline-variant',
  warning: 'bg-secondary-container text-[var(--md-sys-color-on-secondary-container)] border-outline-variant',
  error: 'bg-error-container text-[var(--md-sys-color-on-error-container)] border-outline-variant',
  info: 'bg-tertiary-container text-[var(--md-sys-color-on-tertiary-container)] border-outline-variant',
  default: 'bg-surface-variant text-[var(--md-sys-color-on-surface-variant)] border-outline-variant',
};

export const Badge = ({ className, variant = 'default', children, ...props }) => {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-3 py-1 text-xs font-medium',
        'border',
        variantClasses[variant] || variantClasses.default,
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};


