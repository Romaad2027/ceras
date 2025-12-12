import React from 'react';
import { cn } from '../../lib/utils';
import { Badge } from './Badge';

export const TagInput = ({ value, onChange, placeholder = 'Add and press Enter', validationRegex }) => {
  const [inputValue, setInputValue] = React.useState('');
  const inputRef = React.useRef(null);

  const addTag = React.useCallback(() => {
    const trimmed = inputValue.trim();
    if (!trimmed) return;
    if (validationRegex instanceof RegExp && !validationRegex.test(trimmed)) return;
    if (value.includes(trimmed)) {
      setInputValue('');
      return;
    }
    onChange([...value, trimmed]);
    setInputValue('');
  }, [inputValue, onChange, validationRegex, value]);

  const removeTag = React.useCallback(
    (tagToRemove) => {
      const next = value.filter((t) => t !== tagToRemove);
      onChange(next);
    },
    [onChange, value]
  );

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTag();
    }
  };

  return (
    <div className="w-full">
      <div
        className={cn(
          'w-full rounded-lg bg-surface-variant text-surface-foreground',
          'border border-transparent focus-within:border-primary focus-within:ring-2 focus-within:ring-outline-variant',
          'px-3 py-2 transition-shadow'
        )}
        onClick={() => inputRef.current?.focus()}
      >
        <div className="flex flex-wrap items-center gap-2">
          {value.map((tag) => (
            <Badge key={tag} className="bg-indigo-50 text-indigo-700 rounded-md border-indigo-200">
              <span className="truncate max-w-[14rem]">{tag}</span>
              <button
                type="button"
                aria-label={`Remove ${tag}`}
                onClick={() => removeTag(tag)}
                className="ml-2 inline-flex h-4 w-4 items-center justify-center rounded hover:bg-indigo-100 text-indigo-700"
              >
                <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 6l12 12M18 6L6 18" />
                </svg>
              </button>
            </Badge>
          ))}
          <input
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="min-w-[8rem] flex-1 bg-transparent text-surface-foreground placeholder-[var(--md-sys-color-on-surface-variant)] outline-none"
          />
        </div>
      </div>
    </div>
  );
};

TagInput.displayName = 'TagInput';


