import React from 'react';
import { StatusHistoryItem } from '@/types/api';
import { formatDate, formatDateTime, formatStatusLabel } from '@/lib/formatting';

interface TimelineProps {
  items: StatusHistoryItem[];
}

export function Timeline({ items }: TimelineProps) {
  if (!items || items.length === 0) {
    return <p className="text-sm text-console-muted italic">No history events available.</p>;
  }

  return (
    <div className="flow-root">
      <ul className="-mb-8">
        {items.map((item, idx) => {
          const isLast = idx === items.length - 1;
          return (
            <li key={idx}>
              <div className="relative pb-8">
                {!isLast && (
                  <span
                    className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-console-border"
                    aria-hidden="true"
                  />
                )}
                <div className="relative flex space-x-3">
                  <div>
                    <span className="h-8 w-8 rounded-full bg-console-surface border border-console-border flex items-center justify-center ring-4 ring-console-bg">
                      <span className="h-2 w-2 rounded-full bg-console-accent" />
                    </span>
                  </div>
                  <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                    <div>
                      <p className="text-xs font-medium text-console-text">
                        {item.from_status ? (
                          <>
                            Transitioned from{' '}
                            <span className="font-semibold text-console-muted">{formatStatusLabel(item.from_status)}</span>{' '}
                            to <span className="font-semibold text-console-accent">{formatStatusLabel(item.to_status)}</span>
                          </>
                        ) : (
                          <>
                            Status set to <span className="font-semibold text-console-accent">{formatStatusLabel(item.to_status)}</span>
                          </>
                        )}
                      </p>
                      {item.note && (
                        <p className="mt-1 text-xs text-console-muted bg-console-bg/50 p-2 rounded border border-console-border/50">
                          {item.note}
                        </p>
                      )}
                    </div>
                    <div className="text-right text-xs whitespace-nowrap text-console-muted font-mono">
                      {formatDateTime(item.created_at)}
                    </div>
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
