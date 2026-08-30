import React from 'react';
import { DataTable, Column } from '@/components/ui/data-table';
import { StatusBadge } from '@/components/ui/status-badge';
import { KnowledgeSource } from '@/types/api';
import { formatDate } from '@/lib/formatting';
import { BookOpen, ExternalLink, ShieldCheck } from 'lucide-react';

interface SourceTableProps {
  sources: KnowledgeSource[];
  onSelect: (source: KnowledgeSource) => void;
}

export function SourceTable({ sources, onSelect }: SourceTableProps) {
  const columns: Column<KnowledgeSource>[] = [
    {
      header: 'Source Title',
      accessorKey: 'title',
      cell: (item) => (
        <div className="flex items-center space-x-2">
          <BookOpen className="h-4 w-4 text-indigo-500" />
          <span className="font-bold text-slate-900 dark:text-white truncate max-w-xs">{item.title}</span>
        </div>
      ),
    },
    {
      header: 'Publisher / Department',
      accessorKey: 'publisher',
      cell: (item) => <span className="font-mono text-xs text-slate-600 dark:text-slate-400">{item.publisher || 'Official Govt'}</span>,
    },
    {
      header: 'Trust Level',
      accessorKey: 'trust_level',
      cell: (item) => (
        <span className="inline-flex items-center text-[10px] font-mono px-2 py-0.5 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-300 border border-indigo-500/30 font-bold">
          <ShieldCheck className="h-3 w-3 mr-1" />
          {item.trust_level.toUpperCase()}
        </span>
      ),
    },
    {
      header: 'Verification Status',
      accessorKey: 'verification_status',
      cell: (item) => <StatusBadge status={item.verification_status} />,
    },
    {
      header: 'Ingested Date',
      accessorKey: 'created_at',
      cell: (item) => <span className="font-mono text-slate-600 dark:text-slate-400">{formatDate(item.created_at)}</span>,
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={sources}
      keyExtractor={(item) => item.id}
      onRowClick={onSelect}
      emptyMessage="No knowledge sources registered."
    />
  );
}
