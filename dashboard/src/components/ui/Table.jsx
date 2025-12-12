import { cn } from '../../lib/utils';

export const Table = ({
  className,
  columns = [],
  data = [],
  zebra = false,
  stickyHeader = true,
  onRowClick,
  rowKey = 'id',
  emptyMessage = 'No data available.',
}) => {
  const getRowKey = (row, index) => {
    if (typeof rowKey === 'function') return rowKey(row, index);
    return row?.[rowKey] ?? index;
  };

  return (
    <div
      className={cn(
        'w-full overflow-x-auto rounded-xl bg-surface border border-outline-variant shadow-sm',
        className
      )}
    >
      <table className="min-w-full text-left text-sm text-surface-foreground">
        <thead
          className={cn(
            'text-[var(--md-sys-color-on-surface-variant)]',
            stickyHeader && 'sticky top-0 z-10'
          )}
        >
          <tr className="bg-[var(--md-sys-color-surface-container-high)]">
            {columns.map((col, idx) => (
              <th
                key={idx}
                className={cn(
                  'px-4 py-3 font-semibold uppercase tracking-wider text-xs',
                  idx === 0 && 'rounded-tl-lg',
                  idx === columns.length - 1 && 'rounded-tr-lg'
                )}
                style={{ width: col.width }}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 && (
            <tr>
              <td
                className="px-4 py-6 text-center text-[var(--md-sys-color-on-surface-variant)]"
                colSpan={columns.length || 1}
              >
                {emptyMessage}
              </td>
            </tr>
          )}
          {data.map((row, rowIndex) => (
            <tr
              key={getRowKey(row, rowIndex)}
              className={cn(
                'transition-colors border-b border-outline-variant',
                'hover:bg-[var(--md-sys-color-surface-container-low)]',
                zebra && rowIndex % 2 === 1 ? 'bg-[var(--md-sys-color-surface-container)]' : 'bg-transparent',
                onRowClick && 'cursor-pointer'
              )}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
            >
              {columns.map((col, colIndex) => {
                const value =
                  typeof col.accessor === 'function'
                    ? col.accessor(row)
                    : row?.[col.accessor];
                return (
                  <td key={colIndex} className="px-4 py-3 align-middle text-surface-foreground text-sm">
                    {col.cell ? col.cell(value, row) : value}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};


