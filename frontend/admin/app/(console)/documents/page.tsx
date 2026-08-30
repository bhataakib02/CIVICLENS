'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { DocumentTable } from '@/components/documents/document-table';
import { TableSkeleton } from '@/components/ui/loading-skeleton';
import { getDocuments } from '@/lib/api/documents';
import { DocumentSummary } from '@/types/api';
import { FileText } from 'lucide-react';

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
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      <div className="bg-white dark:bg-slate-900/90 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl space-y-1">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-indigo-500" />
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">Document Verification Queue</h1>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Review OCR output, verify extracted evidence, and confirm document status.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-semibold">
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
