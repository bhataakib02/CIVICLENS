'use client';

import React, { useEffect, useState } from 'react';
import { AuditTable } from '@/components/audit/audit-table';
import { Pagination } from '@/components/ui/pagination';
import { TableSkeleton } from '@/components/ui/loading-skeleton';
import { getAuditLogs } from '@/lib/api/audit';
import { AuditLogPage } from '@/types/api';
import { History, Shield, Lock } from 'lucide-react';

export default function AuditPage() {
  const [data, setData] = useState<AuditLogPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);

  const fetchAuditLogs = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getAuditLogs({ page, page_size: 20 });
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load audit logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, [page]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      <div className="bg-white dark:bg-slate-900/90 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-500" />
            <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">Immutable Audit Log Inspection</h1>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Read-only, append-only system trail. Modification or deletion of audit logs is strictly prohibited.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-3.5 py-2 rounded-2xl">
          <Lock className="h-4 w-4" />
          <span>Strict Read-Only Enforcement</span>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-semibold">
          {error}
        </div>
      )}

      {loading && !data ? (
        <TableSkeleton rows={10} cols={5} />
      ) : data ? (
        <div className="space-y-4">
          <AuditTable logs={data.items} />
          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            onPageChange={setPage}
          />
        </div>
      ) : null}
    </div>
  );
}
