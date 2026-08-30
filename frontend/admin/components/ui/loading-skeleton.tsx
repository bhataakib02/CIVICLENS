import React from 'react';

export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="w-full animate-pulse">
      <div className="h-10 bg-console-elevated/50 rounded-t-lg mb-2" />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center space-x-4 p-4 border-b border-console-border">
          {Array.from({ length: cols }).map((_, j) => (
            <div key={j} className="h-4 bg-console-surface rounded flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="glass-card p-5 animate-pulse">
      <div className="h-4 bg-console-surface rounded w-1/3 mb-4" />
      <div className="h-8 bg-console-elevated rounded w-1/2" />
    </div>
  );
}
