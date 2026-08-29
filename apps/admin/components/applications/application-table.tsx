import React from 'react';
import { DataTable, Column } from '@/components/ui/data-table';
import { StatusBadge } from '@/components/ui/status-badge';
import { ApplicationSummary } from '@/types/api';
import { formatDate } from '@/lib/formatting';

interface ApplicationTableProps {
  applications: ApplicationSummary[];
  onSelect: (app: ApplicationSummary) => void;
}

export function ApplicationTable({ applications, onSelect }: ApplicationTableProps) {
  const columns: Column<ApplicationSummary>[] = [
    {
      header: 'Application No.',
      accessorKey: 'application_number',
      cell: (item) => (
        <span className="font-mono font-medium text-console-accent">{item.application_number}</span>
      ),
    },
    {
      header: 'Status',
      accessorKey: 'status',
      cell: (item) => <StatusBadge status={item.status} />,
    },
    {
      header: 'Created Date',
      accessorKey: 'created_at',
      cell: (item) => <span className="font-mono">{formatDate(item.created_at)}</span>,
    },
    {
      header: 'Submitted Date',
      accessorKey: 'submitted_at',
      cell: (item) => <span className="font-mono">{formatDate(item.submitted_at)}</span>,
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={applications}
      keyExtractor={(item) => item.id}
      onRowClick={onSelect}
      emptyMessage="No applications match the selected criteria."
    />
  );
}
