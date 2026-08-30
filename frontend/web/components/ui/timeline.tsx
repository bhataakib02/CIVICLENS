import React from 'react';
import { StatusBadge } from './status-badge';
import { formatDate } from '@/lib/formatting/date';

export interface TimelineItem {
  id: string;
  status: string;
  note?: string | null;
  timestamp: string;
}

interface TimelineProps {
  items: TimelineItem[];
}

export function Timeline({ items }: TimelineProps) {
  if (!items || items.length === 0) {
    return <p className="text-sm text-slate-500 italic">No history available yet.</p>;
  }

  return (
    <div className="relative pl-6 border-l-2 border-slate-200 space-y-6">
      {items.map((item, index) => (
        <div key={item.id || index} className="relative group">
          <div className="absolute -left-[31px] top-1 w-4 h-4 rounded-full bg-blue-600 border-4 border-white shadow-sm" />
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1">
            <StatusBadge status={item.status} />
            <span className="text-xs text-slate-400 font-mono">{formatDate(item.timestamp)}</span>
          </div>
          {item.note && <p className="text-sm text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100 mt-2">{item.note}</p>}
        </div>
      ))}
    </div>
  );
}
