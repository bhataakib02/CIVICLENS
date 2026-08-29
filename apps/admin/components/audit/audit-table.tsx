import React from 'react';
import { DataTable, Column } from '@/components/ui/data-table';
import { AuditLogEntry } from '@/types/api';
import { formatDateTime } from '@/lib/formatting';
import { History, Shield, User } from 'lucide-react';

interface AuditTableProps {
  logs: AuditLogEntry[];
}

export function AuditTable({ logs }: AuditTableProps) {
  const columns: Column<AuditLogEntry>[] = [
    {
      header: 'Timestamp',
      accessorKey: 'created_at',
      cell: (item) => <span className="font-mono text-console-text text-xs">{formatDateTime(item.created_at)}</span>,
    },
    {
      header: 'Action',
      accessorKey: 'action',
      cell: (item) => (
        <span className="font-mono text-console-accent font-medium text-xs">{item.action}</span>
      ),
    },
    {
      header: 'Entity Type',
      accessorKey: 'entity_type',
      cell: (item) => (
        <span className="inline-flex items-center text-[10px] font-mono px-2 py-0.5 rounded bg-console-surface border border-console-border text-console-muted uppercase">
          {item.entity_type}
        </span>
      ),
    },
    {
      header: 'Actor ID',
      accessorKey: 'actor_user_id',
      cell: (item) => (
        <span className="font-mono text-[11px] text-console-muted">
          {item.actor_user_id ? item.actor_user_id : 'System'}
        </span>
      ),
    },
    {
      header: 'Metadata Diff',
      accessorKey: 'diff',
      cell: (item) => (
        <span className="font-mono text-[10px] text-console-muted truncate max-w-xs block">
          {item.diff ? JSON.stringify(item.diff) : '—'}
        </span>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={logs}
      keyExtractor={(item) => item.id}
      emptyMessage="No audit log entries recorded."
    />
  );
}
