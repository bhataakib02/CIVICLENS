'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { SchemeTable } from '@/components/schemes/scheme-table';
import { TableSkeleton } from '@/components/ui/loading-skeleton';
import { getSchemes } from '@/lib/api/schemes';
import { SchemePage, SchemeSummary } from '@/types/api';
import { Plus, Building } from 'lucide-react';
import { useAuth } from '@/lib/auth/auth-context';
import { hasCapability } from '@/lib/permissions/roles';

export default function SchemesPage() {
  const router = useRouter();
  const { account } = useAuth();
  const [data, setData] = useState<SchemePage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const canCreate = hasCapability(account?.role, 'canEditSchemeDrafts');

  const fetchSchemes = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getSchemes({ page_size: 20 });
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load schemes catalog.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchemes();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-console-text tracking-tight">Scheme Administration Console</h1>
          <p className="text-xs text-console-muted mt-1">Manage public service schemes, versioning, and eligibility rule DSL</p>
        </div>

        {canCreate && (
          <button
            onClick={() => router.push('/schemes/new')}
            className="btn-primary text-xs flex items-center space-x-1.5"
          >
            <Plus className="h-4 w-4" />
            <span>Create New Scheme</span>
          </button>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
          {error}
        </div>
      )}

      {loading && !data ? (
        <TableSkeleton rows={8} cols={4} />
      ) : data ? (
        <SchemeTable
          schemes={data.items}
          onSelect={(s) => router.push(`/schemes/${s.id}`)}
        />
      ) : null}
    </div>
  );
}
