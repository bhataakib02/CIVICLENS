'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { DocumentTable } from '@/components/documents/document-table';
import { TableSkeleton } from '@/components/ui/loading-skeleton';
import { getDocuments } from '@/lib/api/documents';
import { DocumentSummary } from '@/types/api';

export default function DocumentsPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchDocs = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getDocuments();
      setDocuments(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load document records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-console-text tracking-tight">Document Verification Queue</h1>
          <p className="text-xs text-console-muted mt-1">Review OCR output, verify extracted evidence, and confirm document status</p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
          {error}
        </div>
      )}

      {loading ? (
        <TableSkeleton rows={8} cols={5} />
      ) : (
        <DocumentTable
          documents={documents}
          onSelect={(doc) => router.push(`/documents/${doc.id}`)}
        />
      )}
    </div>
  );
}
