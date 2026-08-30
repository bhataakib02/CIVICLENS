'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { CitizenTable } from '@/components/citizens/citizen-table';
import { SearchInput } from '@/components/ui/search-input';
import { Pagination } from '@/components/ui/pagination';
import { TableSkeleton } from '@/components/ui/loading-skeleton';
import { searchCitizens } from '@/lib/api/citizens';
import { CitizenSummaryPage } from '@/types/api';
import { Users, Filter } from 'lucide-react';

export default function CitizensPage() {
  const router = useRouter();
  const [data, setData] = useState<CitizenSummaryPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);

  const fetchCitizens = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await searchCitizens({ q: query || undefined, page, page_size: 15 });
      if (statusFilter !== 'all' && res.items) {
        res.items = res.items.filter((c) => c.status.toLowerCase() === statusFilter.toLowerCase());
      }
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to search citizen records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCitizens();
  }, [query, statusFilter, page]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      {/* Header Banner */}
      <div className="bg-white dark:bg-slate-900/90 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl space-y-1">
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-indigo-500" />
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">Citizen Directory</h1>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Role-restricted citizen lookup, profile governance, and direct account management.
        </p>
      </div>

      {/* Sub-Data Filters Bar */}
      <div className="bg-white dark:bg-slate-900/90 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-lg flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="w-full md:w-80">
          <SearchInput
            value={query}
            onChange={(val) => {
              setQuery(val);
              setPage(1);
            }}
            placeholder="Search by email or phone..."
          />
        </div>

        {/* Status Sub-Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <Filter className="w-3.5 h-3.5 text-indigo-500" /> Filter Status:
          </span>
          {['all', 'active', 'suspended', 'unverified'].map((st) => (
            <button
              key={st}
              onClick={() => {
                setStatusFilter(st);
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold capitalize transition-all border ${
                statusFilter === st
                  ? 'bg-indigo-600 text-white border-indigo-600 shadow-md'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-semibold">
          {error}
        </div>
      )}

      {loading && !data ? (
        <TableSkeleton rows={8} cols={6} />
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
