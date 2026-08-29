import React from 'react';
import { DataTable, Column } from '@/components/ui/data-table';
import { StatusBadge } from '@/components/ui/status-badge';
import { CitizenSummary } from '@/types/api';
import { formatDate } from '@/lib/formatting';

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
        <span className="font-mono text-console-text">{item.email || 'Phone account'}</span>
      ),
    },
    {
      header: 'Masked Phone',
      accessorKey: 'phone_number_masked',
      cell: (item) => (
        <span className="font-mono text-console-muted">{item.phone_number_masked || '—'}</span>
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
      cell: (item) => (
        <div className="flex items-center space-x-2">
          <div className="w-16 bg-console-bg rounded-full h-1.5 overflow-hidden border border-console-border">
            <div
              className="bg-console-accent h-full rounded-full"
              style={{ width: `${Math.min(100, (item.profile_completeness || 0) * 100)}%` }}
            />
          </div>
          <span className="font-mono text-xs text-console-muted">
            {Math.round((item.profile_completeness || 0) * 100)}%
          </span>
        </div>
      ),
    },
    {
      header: 'Registered Date',
      accessorKey: 'created_at',
      cell: (item) => <span className="font-mono">{formatDate(item.created_at)}</span>,
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
