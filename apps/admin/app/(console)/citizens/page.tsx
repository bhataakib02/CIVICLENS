'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { CitizenTable } from '@/components/citizens/citizen-table';
import { SearchInput } from '@/components/ui/search-input';
import { Pagination } from '@/components/ui/pagination';
import { TableSkeleton } from '@/components/ui/loading-skeleton';
import { searchCitizens } from '@/lib/api/citizens';
import { CitizenSummaryPage } from '@/types/api';

export default function CitizensPage() {
  const router = useRouter();
  const [data, setData] = useState<CitizenSummaryPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);

  const fetchCitizens = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await searchCitizens({ q: query || undefined, page, page_size: 15 });
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to search citizen records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCitizens();
  }, [query, page]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-console-text tracking-tight">Citizen Directory</h1>
          <p className="text-xs text-console-muted mt-1">Role-restricted citizen lookup with PII minimization</p>
        </div>
      </div>

      <div className="glass-card p-4 max-w-md">
        <SearchInput
          value={query}
          onChange={(val) => {
            setQuery(val);
            setPage(1);
          }}
          placeholder="Search by email or phone..."
        />
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
          {error}
        </div>
      )}

      {loading && !data ? (
        <TableSkeleton rows={8} cols={5} />
      ) : data ? (
        <div className="space-y-4">
          <CitizenTable
            citizens={data.items}
            onSelect={(c) => router.push(`/citizens/${c.user_id}`)}
          />
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
