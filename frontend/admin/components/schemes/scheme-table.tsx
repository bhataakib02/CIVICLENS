import React from 'react';
import { DataTable, Column } from '@/components/ui/data-table';
import { SchemeSummary } from '@/types/api';
import { Building, Globe, MapPin } from 'lucide-react';

interface SchemeTableProps {
  schemes: SchemeSummary[];
  onSelect: (scheme: SchemeSummary) => void;
}

export function SchemeTable({ schemes, onSelect }: SchemeTableProps) {
  const columns: Column<SchemeSummary>[] = [
    {
      header: 'Canonical Scheme Name',
      accessorKey: 'canonical_name',
      cell: (item) => (
        <div className="flex items-center space-x-2">
          <Building className="h-4 w-4 text-console-accent" />
          <span className="font-semibold text-console-text">{item.canonical_name}</span>
        </div>
      ),
    },
    {
      header: 'Category',
      accessorKey: 'category',
      cell: (item) => <span className="font-mono text-xs">{item.category}</span>,
    },
    {
      header: 'Scope',
      accessorKey: 'scope',
      cell: (item) => (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium border ${
            item.scope === 'central'
              ? 'bg-blue-500/10 text-blue-400 border-blue-500/30'
              : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
          }`}
        >
          {item.scope === 'central' ? <Globe className="h-3 w-3 mr-1" /> : <MapPin className="h-3 w-3 mr-1" />}
          {item.scope.toUpperCase()}
        </span>
      ),
    },
    {
      header: 'Benefits Summary',
      accessorKey: 'benefits_summary',
      cell: (item) => (
        <span className="text-console-muted truncate max-w-xs block">{item.benefits_summary || '—'}</span>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={schemes}
      keyExtractor={(item) => item.id}
      onRowClick={onSelect}
      emptyMessage="No schemes configured."
    />
  );
}
