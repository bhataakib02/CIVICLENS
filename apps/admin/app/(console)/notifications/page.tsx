'use client';

import React, { useEffect, useState } from 'react';
import { NotificationOpsTable } from '@/components/notifications/notification-ops-table';
import { Pagination } from '@/components/ui/pagination';
import { TableSkeleton } from '@/components/ui/loading-skeleton';
import { FilterBar, FilterOption } from '@/components/ui/filter-bar';
import { getNotificationOps, retryNotification } from '@/lib/api/notifications';
import type { NotificationOpsPage } from '@/types/api';
import { Bell } from 'lucide-react';

export default function NotificationOpsPage() {
  const [data, setData] = useState<NotificationOpsPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [channelFilter, setChannelFilter] = useState('');
  const [page, setPage] = useState(1);

  const fetchOps = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getNotificationOps({
        status: statusFilter || undefined,
        channel: channelFilter || undefined,
        page,
        page_size: 20,
      });
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load notification operational logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOps();
  }, [statusFilter, channelFilter, page]);

  const handleRetry = async (id: string) => {
    try {
      await retryNotification(id);
      await fetchOps();
    } catch (err: any) {
      alert(err.message || 'Failed to retry notification delivery.');
    }
  };

  const filterOptions: FilterOption[] = [
    {
      key: 'status',
      label: 'Status',
      value: statusFilter,
      options: [
        { label: 'Failed', value: 'failed' },
        { label: 'Sent', value: 'sent' },
        { label: 'Delivered', value: 'delivered' },
        { label: 'Queued', value: 'queued' },
        { label: 'Pending', value: 'pending' },
      ],
    },
    {
      key: 'channel',
      label: 'Channel',
      value: channelFilter,
      options: [
        { label: 'In-App', value: 'in_app' },
        { label: 'SMS', value: 'sms' },
        { label: 'Email', value: 'email' },
        { label: 'Push', value: 'push' },
      ],
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      <div className="bg-white dark:bg-slate-900/90 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl space-y-1">
        <div className="flex items-center gap-2">
          <Bell className="w-5 h-5 text-indigo-500" />
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">Notification Delivery Operations</h1>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Monitor notification pipeline, inspect delivery error codes, and trigger retries.
        </p>
      </div>

      <div className="bg-white dark:bg-slate-900/90 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-lg">
        <FilterBar
          filters={filterOptions}
          onFilterChange={(key, val) => {
            if (key === 'status') setStatusFilter(val);
            if (key === 'channel') setChannelFilter(val);
            setPage(1);
          }}
          onClearAll={() => {
            setStatusFilter('');
            setChannelFilter('');
            setPage(1);
          }}
        />
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
          <NotificationOpsTable notifications={data.items} onRetry={handleRetry} />
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
