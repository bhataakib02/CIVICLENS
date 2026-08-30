import React from 'react';
import { DataTable, Column } from '@/components/ui/data-table';
import { StatusBadge } from '@/components/ui/status-badge';
import { NotificationOps } from '@/types/api';
import { formatDate } from '@/lib/formatting';
import { Bell, RefreshCw } from 'lucide-react';

interface NotificationOpsTableProps {
  notifications: NotificationOps[];
  onRetry: (id: string) => void;
}

export function NotificationOpsTable({ notifications, onRetry }: NotificationOpsTableProps) {
  const columns: Column<NotificationOps>[] = [
    {
      header: 'Notification ID',
      accessorKey: 'id',
      cell: (item) => <span className="font-mono text-xs text-console-accent">{item.id.slice(0, 8)}...</span>,
    },
    {
      header: 'Channel',
      accessorKey: 'channel',
      cell: (item) => <span className="font-mono uppercase text-xs">{item.channel}</span>,
    },
    {
      header: 'Category',
      accessorKey: 'category',
      cell: (item) => <span className="font-mono text-xs text-console-muted">{item.category}</span>,
    },
    {
      header: 'Status',
      accessorKey: 'status',
      cell: (item) => <StatusBadge status={item.status} />,
    },
    {
      header: 'Failure Code / Attempts',
      accessorKey: 'failure_code',
      cell: (item) => (
        <span className="font-mono text-xs text-red-400">
          {item.failure_code ? `${item.failure_code} (${item.attempts} attempts)` : '—'}
        </span>
      ),
    },
    {
      header: 'Action',
      cell: (item) =>
        item.status === 'failed' ? (
          <button
            onClick={() => onRetry(item.id)}
            className="btn-secondary text-[11px] py-1 px-2.5 flex items-center space-x-1 border-red-500/30 text-red-400 hover:bg-red-500/10"
          >
            <RefreshCw className="h-3 w-3" />
            <span>Retry Delivery</span>
          </button>
        ) : (
          <span className="text-console-muted">—</span>
        ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={notifications}
      keyExtractor={(item) => item.id}
      emptyMessage="No notification logs available."
    />
  );
}
