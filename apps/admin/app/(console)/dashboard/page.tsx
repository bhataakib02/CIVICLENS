'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { MetricCard } from '@/components/ui/metric-card';
import { getDashboardMetrics } from '@/lib/api/system';
import { DashboardMetrics } from '@/types/api';
import {
  FileText,
  AlertTriangle,
  FileCheck,
  Building,
  BookOpen,
  BellOff,
  Users,
  Layers,
  RefreshCw,
  Loader2,
} from 'lucide-react';
import { useAuth } from '@/lib/auth/auth-context';

export default function DashboardPage() {
  const router = useRouter();
  const { account } = useAuth();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchMetrics = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getDashboardMetrics();
      setMetrics(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load operational metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-console-text tracking-tight">Operational Dashboard</h1>
          <p className="text-xs text-console-muted mt-1">Real-time status of backend operations & queues</p>
        </div>
        <button
          onClick={fetchMetrics}
          disabled={loading}
          className="btn-secondary text-xs flex items-center space-x-2"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
          {error}
        </div>
      )}

      {loading && !metrics ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-console-accent" />
        </div>
      ) : metrics ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Pending Application Review"
            value={metrics.applications_pending_review}
            subtitle="Submitted applications awaiting worker review"
            icon={FileText}
            variant="info"
            onClick={() => router.push('/applications?status=submitted')}
          />

          <MetricCard
            title="Action Required Applications"
            value={metrics.applications_action_required}
            subtitle="Waiting for citizen response"
            icon={AlertTriangle}
            variant="warning"
            onClick={() => router.push('/applications?status=action_required')}
          />

          <MetricCard
            title="Documents Needing Verification"
            value={metrics.documents_verification_required}
            subtitle="Extracted document evidence requiring verification"
            icon={FileCheck}
            variant="warning"
            onClick={() => router.push('/documents')}
          />

          <MetricCard
            title="Scheme Drafts Pending Review"
            value={metrics.scheme_drafts_awaiting_review}
            subtitle="Versions awaiting four-eyes publish approval"
            icon={Building}
            variant="info"
            onClick={() => router.push('/schemes')}
          />

          <MetricCard
            title="Pending Knowledge Sources"
            value={metrics.knowledge_sources_pending}
            subtitle="Sources needing verification"
            icon={BookOpen}
            variant="neutral"
            onClick={() => router.push('/knowledge')}
          />

          <MetricCard
            title="Failed Notifications"
            value={metrics.notifications_failed}
            subtitle="Delivery failures requiring inspection"
            icon={BellOff}
            variant="danger"
            onClick={() => router.push('/notifications')}
          />

          <MetricCard
            title="Total Registered Citizens"
            value={metrics.total_citizens}
            subtitle="Citizen user accounts in system"
            icon={Users}
            variant="neutral"
            onClick={() => router.push('/citizens')}
          />

          <MetricCard
            title="Total Applications"
            value={metrics.total_applications}
            subtitle="All-time case file count"
            icon={Layers}
            variant="neutral"
            onClick={() => router.push('/applications')}
          />
        </div>
      ) : null}
    </div>
  );
}
