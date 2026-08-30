import React from 'react';

export interface FilterOption {
  key: string;
  label: string;
  options: Array<{ label: string; value: string }>;
  value: string;
}

interface FilterBarProps {
  filters: FilterOption[];
  onFilterChange: (key: string, value: string) => void;
  onClearAll?: () => void;
}

export function FilterBar({ filters, onFilterChange, onClearAll }: FilterBarProps) {
  const hasActiveFilters = filters.some((f) => f.value !== '');

  return (
    <div className="flex flex-wrap items-center gap-3">
      {filters.map((filter) => (
        <div key={filter.key} className="flex items-center space-x-1.5">
          <label className="text-xs font-medium text-console-muted">{filter.label}:</label>
          <select
            value={filter.value}
            onChange={(e) => onFilterChange(filter.key, e.target.value)}
            className="input-field text-xs py-1.5 px-2 bg-console-surface"
          >
            <option value="">All</option>
            {filter.options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      ))}

      {hasActiveFilters && onClearAll && (
        <button
          onClick={onClearAll}
          className="text-xs text-console-accent hover:underline ml-2"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
