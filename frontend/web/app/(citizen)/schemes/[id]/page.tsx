'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { getSchemeById } from '@/lib/api/schemes';
import { SchemeDetail } from '@/types/api';
import { SchemeDetailView } from '@/components/schemes/scheme-detail-view';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert } from '@/components/ui/alert';

export default function SchemeDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [scheme, setScheme] = useState<SchemeDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    async function loadScheme() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getSchemeById(id);
        setScheme(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load scheme details.');
      } finally {
        setIsLoading(false);
      }
    }
    loadScheme();
  }, [id]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-40" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (error || !scheme) {
    return (
      <Alert type="error" title="Scheme Error">
        {error || 'Scheme not found.'}
      </Alert>
    );
  }

  return <SchemeDetailView scheme={scheme} />;
}
