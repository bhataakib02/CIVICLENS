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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-console-text tracking-tight">Notification Delivery Operations</h1>
          <p className="text-xs text-console-muted mt-1">Monitor notification pipeline, inspect delivery error codes, and trigger retries</p>
        </div>
      </div>

      <div className="glass-card p-4">
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
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
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
