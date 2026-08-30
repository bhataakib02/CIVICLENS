'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ApplicationTable } from '@/components/applications/application-table';
import { FilterBar, FilterOption } from '@/components/ui/filter-bar';
import { Pagination } from '@/components/ui/pagination';
import { TableSkeleton } from '@/components/ui/loading-skeleton';
import { getApplications } from '@/lib/api/applications';
import { ApplicationPage, ApplicationSummary } from '@/types/api';

export default function ApplicationsPage() {
  const router = useRouter();
  const [data, setData] = useState<ApplicationPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);

  const fetchApplications = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getApplications({ status: statusFilter || undefined, page, page_size: 15 });
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load applications.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, [statusFilter, page]);

  const filterOptions: FilterOption[] = [
    {
      key: 'status',
      label: 'Status',
      value: statusFilter,
      options: [
        { label: 'Submitted', value: 'submitted' },
        { label: 'Under Review', value: 'under_review' },
        { label: 'Action Required', value: 'action_required' },
        { label: 'Approved', value: 'approved' },
        { label: 'Rejected', value: 'rejected' },
        { label: 'Draft', value: 'draft' },
        { label: 'Completed', value: 'completed' },
      ],
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-console-text tracking-tight">Application Queue</h1>
          <p className="text-xs text-console-muted mt-1">Operational case management and review queue</p>
        </div>
      </div>

      <div className="glass-card p-4">
        <FilterBar
          filters={filterOptions}
          onFilterChange={(key, val) => {
            if (key === 'status') setStatusFilter(val);
            setPage(1);
          }}
          onClearAll={() => {
            setStatusFilter('');
            setPage(1);
          }}
        />
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
          {error}
        </div>
      )}

      {loading && !data ? (
        <TableSkeleton rows={8} cols={4} />
      ) : data ? (
        <div className="space-y-4">
          <ApplicationTable
            applications={data.items}
            onSelect={(app) => router.push(`/applications/${app.id}`)}
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
