'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { MetricCard } from '@/components/ui/metric-card';
import { getDashboardMetrics } from '@/lib/api/system';
import { getApplications } from '@/lib/api/applications';
import { getAuditLogs } from '@/lib/api/audit';
import { DashboardMetrics, ApplicationSummary, AuditLogEntry } from '@/types/api';
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
  ShieldCheck,
  Activity,
  PlusCircle,
  ExternalLink,
  Cpu,
  CheckCircle2,
  Clock,
  ArrowRight
} from 'lucide-react';
import { useAuth } from '@/lib/auth/auth-context';

export default function DashboardPage() {
  const router = useRouter();
  const { account } = useAuth();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [recentApplications, setRecentApplications] = useState<ApplicationSummary[]>([]);
  const [recentAuditLogs, setRecentAuditLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [lastRefreshed, setLastRefreshed] = useState<string>('');

  const fetchDashboardData = async () => {
    setLoading(true);
    setError('');
    try {
      const [mRes, appRes, auditRes] = await Promise.allSettled([
        getDashboardMetrics(),
        getApplications({ page: 1, page_size: 5 }),
        getAuditLogs({ page: 1, page_size: 6 }),
      ]);

      if (mRes.status === 'fulfilled') setMetrics(mRes.value);
      if (appRes.status === 'fulfilled') setRecentApplications(appRes.value.items || []);
      if (auditRes.status === 'fulfilled') setRecentAuditLogs(auditRes.value.items || []);

      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err: any) {
      setError(err.message || 'Failed to load operational metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  return (
    <div className="space-y-8">
      {/* Top Header & Environment Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-console-surface p-6 rounded-2xl border border-console-border shadow-lg">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-console-text tracking-tight">Operational Dashboard</h1>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span>
              SYSTEM HEALTHY
            </span>
          </div>
          <p className="text-xs text-console-muted mt-1">
            Real-time status of backend operations, four-eyes review queues & system telemetry
          </p>
        </div>

        <div className="flex items-center gap-3">
          {lastRefreshed && (
            <span className="text-[11px] text-console-muted font-mono hidden sm:inline">
              Refreshed: {lastRefreshed}
            </span>
          )}
          <button
            onClick={fetchDashboardData}
            disabled={loading}
            className="btn-secondary text-xs flex items-center space-x-2"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Telemetry</span>
          </button>
        </div>
      </div>

      {/* Quick Action Shortcuts Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Link
          href="/schemes/new"
          className="flex items-center gap-2.5 p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 hover:bg-indigo-500/20 transition-all text-xs font-semibold text-indigo-300 group"
        >
          <PlusCircle className="w-4 h-4 text-indigo-400 group-hover:scale-110 transition-transform" />
          <span>New Scheme Draft</span>
        </Link>
        <Link
          href="/applications?status=submitted"
          className="flex items-center gap-2.5 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 hover:bg-amber-500/20 transition-all text-xs font-semibold text-amber-300 group"
        >
          <FileText className="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform" />
          <span>Review Submissions</span>
        </Link>
        <Link
          href="/citizens"
          className="flex items-center gap-2.5 p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 hover:bg-blue-500/20 transition-all text-xs font-semibold text-blue-300 group"
        >
          <Users className="w-4 h-4 text-blue-400 group-hover:scale-110 transition-transform" />
          <span>Lookup Citizens</span>
        </Link>
        <Link
          href="/audit"
          className="flex items-center gap-2.5 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/20 transition-all text-xs font-semibold text-emerald-300 group"
        >
          <ShieldCheck className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
          <span>Audit Logs</span>
        </Link>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
          {error}
        </div>
      )}

      {/* Main Metric Cards Grid */}
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

      {/* Sub-grid: Recent Applications & System Services Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Applications Needing Action */}
        <div className="lg:col-span-2 bg-console-surface border border-console-border rounded-2xl p-6 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-indigo-400" />
              <h2 className="text-sm font-bold text-console-text">Recent Application Queue</h2>
            </div>
            <Link
              href="/applications"
              className="text-xs text-console-accent hover:underline flex items-center gap-1 font-semibold"
            >
              <span>View All Applications</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {recentApplications.length === 0 ? (
            <div className="text-center py-8 text-console-muted text-xs">
              No recent applications in queue.
            </div>
          ) : (
            <div className="space-y-2.5">
              {recentApplications.map((app) => (
                <div
                  key={app.id}
                  className="flex items-center justify-between p-3 rounded-xl bg-console-bg border border-console-border/60 text-xs hover:border-console-border transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-semibold text-console-text">
                        App #{app.id.slice(0, 8)}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-console-elevated text-console-muted">
                        {app.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-console-muted">
                      App Num: <span className="font-mono">{app.application_number || app.id.slice(0, 8)}</span>
                    </p>
                  </div>

                  <Link
                    href={`/applications/${app.id}`}
                    className="btn-secondary text-[11px] py-1.5 px-3 flex items-center gap-1"
                  >
                    <span>Inspect</span>
                    <ExternalLink className="w-3 h-3" />
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* System Services & Security Status */}
        <div className="bg-console-surface border border-console-border rounded-2xl p-6 shadow-lg space-y-4">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-bold text-console-text">System Services</h2>
          </div>

          <div className="space-y-3">
            <div className="p-3 rounded-xl bg-console-bg border border-console-border/60 flex items-center justify-between text-xs">
              <div className="space-y-0.5">
                <p className="font-semibold text-console-text">Deterministic AST Engine</p>
                <p className="text-[10px] text-console-muted">Rule compiler & evaluator</p>
              </div>
              <span className="flex items-center text-[10px] text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-1 rounded-md border border-emerald-500/20">
                <CheckCircle2 className="w-3 h-3 mr-1" /> ACTIVE
              </span>
            </div>

            <div className="p-3 rounded-xl bg-console-bg border border-console-border/60 flex items-center justify-between text-xs">
              <div className="space-y-0.5">
                <p className="font-semibold text-console-text">Document Intelligence OCR</p>
                <p className="text-[10px] text-console-muted">Magic bytes & SHA256 deduplication</p>
              </div>
              <span className="flex items-center text-[10px] text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-1 rounded-md border border-emerald-500/20">
                <CheckCircle2 className="w-3 h-3 mr-1" /> ACTIVE
              </span>
            </div>

            <div className="p-3 rounded-xl bg-console-bg border border-console-border/60 flex items-center justify-between text-xs">
              <div className="space-y-0.5">
                <p className="font-semibold text-console-text">Four-Eyes Governance</p>
                <p className="text-[10px] text-console-muted">Dual authorization policy</p>
              </div>
              <span className="flex items-center text-[10px] text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-1 rounded-md border border-emerald-500/20">
                <ShieldCheck className="w-3 h-3 mr-1" /> ENFORCED
              </span>
            </div>

            <div className="p-3 rounded-xl bg-console-bg border border-console-border/60 flex items-center justify-between text-xs">
              <div className="space-y-0.5">
                <p className="font-semibold text-console-text">Realtime Outbox Bus</p>
                <p className="text-[10px] text-console-muted">WebSocket event dispatcher</p>
              </div>
              <span className="flex items-center text-[10px] text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-1 rounded-md border border-emerald-500/20">
                <CheckCircle2 className="w-3 h-3 mr-1" /> ONLINE
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Audit Log Activity Feed */}
      <div className="bg-console-surface border border-console-border rounded-2xl p-6 shadow-lg space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-console-accent" />
            <h2 className="text-sm font-bold text-console-text">Recent Operational Audit Stream</h2>
          </div>
          <Link
            href="/audit"
            className="text-xs text-console-accent hover:underline flex items-center gap-1 font-semibold"
          >
            <span>View Full Audit Log</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {recentAuditLogs.length === 0 ? (
          <div className="text-center py-6 text-console-muted text-xs">
            No audit activity recorded yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {recentAuditLogs.map((log) => (
              <div
                key={log.id}
                className="p-3 rounded-xl bg-console-bg border border-console-border/60 space-y-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-console-accent uppercase tracking-wider text-[10px]">
                    {log.action}
                  </span>
                  <span className="text-[10px] text-console-muted font-mono">
                    {new Date(log.created_at).toLocaleTimeString()}
                  </span>
                </div>
                <div className="text-[11px] text-console-muted space-y-0.5 font-mono">
                  <p>Entity: <span className="text-console-text">{log.entity_type}</span></p>
                  <p>Actor: <span className="text-console-text">{log.actor_user_id ? log.actor_user_id.slice(0, 8) + '...' : 'System'}</span></p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
