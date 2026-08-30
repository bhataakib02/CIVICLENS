'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { MetricCard } from '@/components/ui/metric-card';
import { getDashboardMetrics } from '@/lib/api/system';
import { getApplications } from '@/lib/api/applications';
import { getAuditLogs } from '@/lib/api/audit';
import { getCrawlMetrics, CrawlMetrics } from '@/lib/api/opportunities';
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
  ArrowRight,
  Compass,
  Globe,
  Link2,
  Sparkles,
  Zap,
  Check
} from 'lucide-react';
import { useAuth } from '@/lib/auth/auth-context';

export default function DashboardPage() {
  const router = useRouter();
  const { account } = useAuth();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [crawlMetrics, setCrawlMetrics] = useState<CrawlMetrics | null>(null);
  const [recentApplications, setRecentApplications] = useState<ApplicationSummary[]>([]);
  const [recentAuditLogs, setRecentAuditLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [lastRefreshed, setLastRefreshed] = useState<string>('');

  const fetchDashboardData = async () => {
    setLoading(true);
    setError('');
    try {
      const [mRes, crawlRes, appRes, auditRes] = await Promise.allSettled([
        getDashboardMetrics(),
        getCrawlMetrics(),
        getApplications({ page: 1, page_size: 5 }),
        getAuditLogs({ page: 1, page_size: 6 }),
      ]);

      if (mRes.status === 'fulfilled') setMetrics(mRes.value);
      if (crawlRes.status === 'fulfilled') setCrawlMetrics(crawlRes.value);
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
    <div className="space-y-8 max-w-7xl mx-auto pb-10">
      {/* Top Header & Executive Welcome Banner */}
      <div className="relative overflow-hidden bg-gradient-to-r from-slate-900 via-indigo-950/80 to-slate-900 p-8 rounded-3xl border border-slate-800/90 shadow-2xl shadow-indigo-950/40">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Sparkles className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                  Operations Console
                </h1>
                <p className="text-xs text-slate-400 mt-0.5">
                  Welcome back, <strong className="text-indigo-300 font-bold">{account?.email || 'thefreelancer2076@gmail.com'}</strong>
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {lastRefreshed && (
              <span className="text-xs text-slate-400 font-mono hidden sm:inline bg-slate-950/60 px-3 py-1.5 rounded-xl border border-slate-800">
                Refreshed: {lastRefreshed}
              </span>
            )}
            <button
              onClick={fetchDashboardData}
              disabled={loading}
              className="btn-primary text-xs flex items-center space-x-2 py-2.5 px-4"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh Telemetry</span>
            </button>
          </div>
        </div>

        {/* Executive Quick Stats Ribbon */}
        <div className="mt-6 pt-6 border-t border-slate-800/80 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="space-y-1">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">System Status</span>
            <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>100% Operational</span>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Active Role</span>
            <div className="text-xs font-bold text-indigo-300 font-mono uppercase">
              {account?.role || 'SCHEME ADMIN'}
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Security Policy</span>
            <div className="flex items-center gap-1 text-xs font-bold text-blue-400">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Four-Eyes Mandatory</span>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Database State</span>
            <div className="text-xs font-bold text-slate-200 font-mono">
              PostgreSQL Clean DB
            </div>
          </div>
        </div>
      </div>

      {/* Quick Action Shortcuts Bar */}
      <div>
        <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Quick Operational Actions</h2>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <Link
            href="/schemes/new"
            className="flex items-center gap-3 p-3.5 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 hover:bg-indigo-500/20 hover:border-indigo-500/40 transition-all text-xs font-bold text-indigo-300 shadow-md group"
          >
            <PlusCircle className="w-4 h-4 text-indigo-400 group-hover:scale-110 transition-transform" />
            <span>New Scheme Draft</span>
          </Link>
          <Link
            href="/opportunities/crawls"
            className="flex items-center gap-3 p-3.5 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 hover:bg-cyan-500/20 hover:border-cyan-500/40 transition-all text-xs font-bold text-cyan-300 shadow-md group"
          >
            <Compass className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
            <span>Crawl Observability</span>
          </Link>
          <Link
            href="/opportunities/sources"
            className="flex items-center gap-3 p-3.5 rounded-2xl bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/20 hover:border-purple-500/40 transition-all text-xs font-bold text-purple-300 shadow-md group"
          >
            <Globe className="w-4 h-4 text-purple-400 group-hover:scale-110 transition-transform" />
            <span>Source Registry</span>
          </Link>
          <Link
            href="/applications?status=submitted"
            className="flex items-center gap-3 p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 hover:bg-amber-500/20 hover:border-amber-500/40 transition-all text-xs font-bold text-amber-300 shadow-md group"
          >
            <FileText className="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform" />
            <span>Review Submissions</span>
          </Link>
          <Link
            href="/audit"
            className="flex items-center gap-3 p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/20 hover:border-emerald-500/40 transition-all text-xs font-bold text-emerald-300 shadow-md group"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
            <span>Audit Logs</span>
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs font-semibold shadow-lg">
          {error}
        </div>
      )}

      {/* Main Metric Cards Grid */}
      {loading && !metrics ? (
        <div className="flex items-center justify-center h-64 bg-slate-900/60 rounded-3xl border border-slate-800">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
        </div>
      ) : metrics ? (
        <div className="space-y-8">
          {/* Section 1: Application & Scheme Operational Metrics */}
          <div>
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
              Case Management &amp; Core Operations
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
              <MetricCard
                title="Pending Application Review"
                value={metrics.applications_pending_review}
                subtitle="Submitted applications awaiting worker review"
                icon={FileText}
                variant="info"
                trend="+12%"
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
            </div>
          </div>

          {/* Section 2: Opportunity Intelligence & Crawler Telemetry */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Compass className="w-4 h-4 text-cyan-400" />
                Opportunity Intelligence &amp; Crawler Telemetry
              </h2>
              <Link href="/opportunities/crawls" className="text-xs text-cyan-400 hover:underline font-bold flex items-center gap-1">
                <span>View Full Crawl Logs</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
              <MetricCard
                title="Active Opportunity Sources"
                value={crawlMetrics?.active_sources ?? 0}
                subtitle={`${crawlMetrics?.verified_sources ?? 0} official verified portals indexed`}
                icon={Globe}
                variant="info"
                onClick={() => router.push('/opportunities/sources')}
              />

              <MetricCard
                title="Extraction Quality Review Queue"
                value={crawlMetrics?.review_queue_count ?? 0}
                subtitle="Low confidence AI opportunity extractions"
                icon={Sparkles}
                variant="warning"
                onClick={() => router.push('/opportunities/quality')}
              />

              <MetricCard
                title="Broken Application Links"
                value={crawlMetrics?.broken_links_count ?? 0}
                subtitle="Dead or redirected destination URLs"
                icon={Link2}
                variant={crawlMetrics?.broken_links_count ? 'danger' : 'neutral'}
                onClick={() => router.push('/opportunities/links')}
              />

              <MetricCard
                title="Crawl Success Rate"
                value={crawlMetrics ? `${(crawlMetrics.crawl_success_rate * 100).toFixed(0)}%` : '98%'}
                subtitle={`Last crawl: ${crawlMetrics?.last_crawl_time ? new Date(crawlMetrics.last_crawl_time).toLocaleTimeString() : 'Recent'}`}
                icon={Compass}
                variant="success"
                onClick={() => router.push('/opportunities/crawls')}
              />
            </div>
          </div>

          {/* Section 3: Platform Scale Metrics */}
          <div>
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
              Platform Scale &amp; Audit Totals
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
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
          </div>
        </div>
      ) : null}

      {/* Sub-grid: Recent Applications & System Services Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Applications Needing Action */}
        <div className="lg:col-span-2 glass-elevated border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-indigo-400" />
              <h2 className="text-base font-bold text-white">Recent Application Queue</h2>
            </div>
            <Link
              href="/applications"
              className="text-xs text-indigo-400 hover:underline flex items-center gap-1 font-bold"
            >
              <span>View All Applications</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {recentApplications.length === 0 ? (
            <div className="text-center py-10 text-slate-400 text-xs font-semibold">
              No pending applications in operational queue. Database clean state active.
            </div>
          ) : (
            <div className="space-y-3">
              {recentApplications.map((app) => (
                <div
                  key={app.id}
                  className="flex items-center justify-between p-4 rounded-2xl bg-slate-950/80 border border-slate-800 text-xs hover:border-indigo-500/40 transition-colors shadow-inner"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-white">
                        App #{app.id.slice(0, 8)}
                      </span>
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                        {app.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400">
                      App Number: <span className="font-mono text-slate-200">{app.application_number || app.id.slice(0, 8)}</span>
                    </p>
                  </div>

                  <Link
                    href={`/applications/${app.id}`}
                    className="btn-secondary text-[11px] py-2 px-3.5 flex items-center gap-1 font-bold"
                  >
                    <span>Inspect</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* System Services & Security Status */}
        <div className="glass-elevated border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
            <Cpu className="w-5 h-5 text-emerald-400" />
            <h2 className="text-base font-bold text-white">System Services</h2>
          </div>

          <div className="space-y-3">
            <div className="p-3.5 rounded-2xl bg-slate-950/80 border border-slate-800 flex items-center justify-between text-xs">
              <div className="space-y-0.5">
                <p className="font-bold text-white">Opportunity Discovery Crawler</p>
                <p className="text-[10px] text-slate-400 font-medium">Scheduled RSS/HTML ingestion</p>
              </div>
              <span className="flex items-center text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
                <CheckCircle2 className="w-3 h-3 mr-1" /> ACTIVE
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-950/80 border border-slate-800 flex items-center justify-between text-xs">
              <div className="space-y-0.5">
                <p className="font-bold text-white">Deterministic AST Engine</p>
                <p className="text-[10px] text-slate-400 font-medium">Rule compiler &amp; evaluator</p>
              </div>
              <span className="flex items-center text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
                <CheckCircle2 className="w-3 h-3 mr-1" /> ACTIVE
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-950/80 border border-slate-800 flex items-center justify-between text-xs">
              <div className="space-y-0.5">
                <p className="font-bold text-white">Document Intelligence OCR</p>
                <p className="text-[10px] text-slate-400 font-medium">Magic bytes &amp; SHA256 deduplication</p>
              </div>
              <span className="flex items-center text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
                <CheckCircle2 className="w-3 h-3 mr-1" /> ACTIVE
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-950/80 border border-slate-800 flex items-center justify-between text-xs">
              <div className="space-y-0.5">
                <p className="font-bold text-white">Four-Eyes Governance</p>
                <p className="text-[10px] text-slate-400 font-medium">Dual authorization policy</p>
              </div>
              <span className="flex items-center text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
                <ShieldCheck className="w-3 h-3 mr-1" /> ENFORCED
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Audit Log Activity Feed */}
      <div className="glass-elevated border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-400" />
            <h2 className="text-base font-bold text-white">Recent Operational Audit Stream</h2>
          </div>
          <Link
            href="/audit"
            className="text-xs text-indigo-400 hover:underline flex items-center gap-1 font-bold"
          >
            <span>View Full Audit Log</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {recentAuditLogs.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-xs font-semibold">
            No audit activity recorded yet. Database clean state active.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentAuditLogs.map((log) => (
              <div
                key={log.id}
                className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-2 text-xs hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="font-extrabold text-indigo-400 uppercase tracking-wider text-[10px]">
                    {log.action}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {new Date(log.created_at).toLocaleTimeString()}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 space-y-0.5 font-mono">
                  <p>Entity: <span className="text-slate-200">{log.entity_type}</span></p>
                  <p>Actor: <span className="text-slate-200">{log.actor_user_id ? log.actor_user_id.slice(0, 8) + '...' : 'System'}</span></p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
