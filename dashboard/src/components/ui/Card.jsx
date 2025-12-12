import { cn } from '../../lib/utils';

export const Card = ({ className, children, ...props }) => {
  return (
    <div
      className={cn(
        'rounded-xl bg-[var(--md-sys-color-surface-container-lowest)] text-surface-foreground border border-outline-variant shadow-sm hover:shadow-md transition-shadow duration-200',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader = ({ className, children, ...props }) => {
  return (
    <div
      className={cn(
        'px-6 py-4 rounded-t-xl',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardContent = ({ className, children, ...props }) => {
  return (
    <div className={cn('p-6', className)} {...props}>
      {children}
    </div>
  );
};


