import React from 'react';
import { DataTable, Column } from '@/components/ui/data-table';
import { StatusBadge } from '@/components/ui/status-badge';
import { DocumentSummary } from '@/types/api';
import { formatDate } from '@/lib/formatting';
import { FileText } from 'lucide-react';

interface DocumentTableProps {
  documents: DocumentSummary[];
  onSelect: (doc: DocumentSummary) => void;
}

export function DocumentTable({ documents, onSelect }: DocumentTableProps) {
  const columns: Column<DocumentSummary>[] = [
    {
      header: 'Filename',
      accessorKey: 'filename',
      cell: (item) => (
        <div className="flex items-center space-x-2">
          <FileText className="h-4 w-4 text-console-accent" />
          <span className="font-medium text-console-text">{item.filename}</span>
        </div>
      ),
    },
    {
      header: 'Document Type',
      accessorKey: 'document_type',
      cell: (item) => <span className="font-mono uppercase text-xs">{item.document_type}</span>,
    },
    {
      header: 'Status',
      accessorKey: 'status',
      cell: (item) => <StatusBadge status={item.status} />,
    },
    {
      header: 'Size',
      accessorKey: 'size_bytes',
      cell: (item) => <span className="font-mono">{Math.round((item.size_bytes || 0) / 1024)} KB</span>,
    },
    {
      header: 'Uploaded Date',
      accessorKey: 'uploaded_at',
      cell: (item) => <span className="font-mono">{formatDate(item.uploaded_at)}</span>,
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={documents}
      keyExtractor={(item) => item.id}
      onRowClick={onSelect}
      emptyMessage="No documents found."
    />
  );
}
