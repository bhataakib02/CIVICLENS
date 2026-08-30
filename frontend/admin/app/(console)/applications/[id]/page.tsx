'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ApplicationDetailView } from '@/components/applications/application-detail';
import { getApplication } from '@/lib/api/applications';
import { ApplicationDetail } from '@/types/api';
import { ArrowLeft, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function ApplicationDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [app, setApp] = useState<ApplicationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchDetail = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getApplication(id);
      setApp(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load application detail.');
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
        <Link href="/applications" className="btn-secondary text-xs p-2">
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-console-text tracking-tight">Case File Detail</h1>
          <p className="text-xs text-console-muted">ID: {id}</p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
          {error}
        </div>
      )}

      {loading && !app ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-console-accent" />
        </div>
      ) : app ? (
        <ApplicationDetailView application={app} onRefresh={fetchDetail} />
      ) : null}
    </div>
  );
}
