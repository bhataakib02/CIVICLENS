'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { DocumentViewer } from '@/components/documents/document-viewer';
import { VerificationPanel } from '@/components/documents/verification-panel';
import { getDocumentDetail } from '@/lib/api/documents';
import { DocumentDetail } from '@/types/api';
import { ArrowLeft, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function DocumentDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchDetail = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getDocumentDetail(id);
      setDoc(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load document detail.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) fetchDetail();
  }, [id]);

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Link href="/documents" className="btn-secondary text-xs p-2">
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-console-text tracking-tight">Document Evidence Review</h1>
          <p className="text-xs text-console-muted">ID: {id}</p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
          {error}
        </div>
      )}

      {loading && !doc ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-console-accent" />
        </div>
      ) : doc ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <DocumentViewer documentId={doc.id} filename={doc.filename} />
          <VerificationPanel document={doc} onRefresh={fetchDetail} />
        </div>
      ) : null}
    </div>
  );
}
