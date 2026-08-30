import React from 'react';
import Link from 'next/link';
import { DataTable, Column } from '@/components/ui/data-table';
import { StatusBadge } from '@/components/ui/status-badge';
import { CitizenSummary } from '@/types/api';
import { formatDate } from '@/lib/formatting';
import { Eye, FilePlus, ChevronRight } from 'lucide-react';

interface CitizenTableProps {
  citizens: CitizenSummary[];
  onSelect: (c: CitizenSummary) => void;
}

export function CitizenTable({ citizens, onSelect }: CitizenTableProps) {
  const columns: Column<CitizenSummary>[] = [
    {
      header: 'Email / Handle',
      accessorKey: 'email',
      cell: (item) => (
        <div className="font-mono text-slate-900 dark:text-white font-semibold">
          {item.email || 'Phone account'}
        </div>
      ),
    },
    {
      header: 'Masked Phone',
      accessorKey: 'phone_number_masked',
      cell: (item) => (
        <span className="font-mono text-slate-600 dark:text-slate-300 font-medium">
          {item.phone_number_masked || '—'}
        </span>
      ),
    },
    {
      header: 'Status',
      accessorKey: 'status',
      cell: (item) => <StatusBadge status={item.status} />,
    },
    {
      header: 'Profile Completeness',
      accessorKey: 'profile_completeness',
      cell: (item) => {
        const pct = Math.round((item.profile_completeness || 0) * 100);
        return (
          <div className="flex items-center space-x-2.5">
            <div className="w-20 bg-slate-200 dark:bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-300 dark:border-slate-700">
              <div
                className="bg-indigo-600 dark:bg-indigo-500 h-full rounded-full transition-all"
                style={{ width: `${Math.min(100, pct)}%` }}
              />
            </div>
            <span className="font-mono text-xs font-bold text-slate-700 dark:text-slate-300">
              {pct}%
            </span>
          </div>
        );
      },
    },
    {
      header: 'Registered Date',
      accessorKey: 'created_at',
      cell: (item) => (
        <span className="font-mono text-slate-600 dark:text-slate-400">
          {formatDate(item.created_at)}
        </span>
      ),
    },
    {
      header: 'Actions',
      cell: (item) => (
        <div className="flex items-center space-x-2" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => onSelect(item)}
            className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-indigo-500/10 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-500/20 dark:hover:bg-indigo-500/30 border border-indigo-500/30 transition-all"
            title="Inspect Citizen Profile"
          >
            <Eye className="w-3.5 h-3.5" />
            <span>View</span>
          </button>
          <Link
            href={`/assisted-citizens?id=${item.user_id}`}
            className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/20 dark:hover:bg-emerald-500/30 border border-emerald-500/30 transition-all"
            title="Assist Citizen Scheme Application"
          >
            <FilePlus className="w-3.5 h-3.5" />
            <span>Assist</span>
          </Link>
        </div>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={citizens}
      keyExtractor={(item) => item.user_id}
      onRowClick={onSelect}
      emptyMessage="No citizen records found."
    />
  );
}
