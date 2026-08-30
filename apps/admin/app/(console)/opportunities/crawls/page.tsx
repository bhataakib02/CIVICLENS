'use client';

import React, { useState, useEffect } from 'react';
import { getCrawlRuns, getCrawlMetrics, CrawlRun, CrawlMetrics } from '@/lib/api/opportunities';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert } from '@/components/ui/alert';
import { Compass, Sparkles, Globe, Activity } from 'lucide-react';

export default function CrawlObservabilityPage() {
  const [runs, setRuns] = useState<CrawlRun[]>([]);
  const [metrics, setMetrics] = useState<CrawlMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadObservability() {
      setIsLoading(true);
      try {
        const [runsData, metricsData] = await Promise.all([getCrawlRuns(), getCrawlMetrics()]);
        setRuns(runsData);
        setMetrics(metricsData);
      } catch (err: any) {
        setError(err.message || 'Failed to load observability metrics.');
      } finally {
        setIsLoading(false);
      }
    }
    loadObservability();
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-slate-900/90 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl space-y-1">
        <div className="flex items-center gap-2">
          <Compass className="w-5 h-5 text-cyan-500" />
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">Crawl Observability &amp; Metrics</h1>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Monitor 30-minute discovery scheduler execution logs, success rates, and items discovered.
        </p>
      </div>

      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-slate-900/90 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-lg">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Active Sources</span>
            <span className="text-2xl font-extrabold text-slate-900 dark:text-white mt-1 block font-mono">{metrics.active_sources}</span>
          </div>
          <div className="bg-white dark:bg-slate-900/90 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-lg">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Verified Portals</span>
            <span className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-1 block font-mono">{metrics.verified_sources}</span>
          </div>
          <div className="bg-white dark:bg-slate-900/90 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-lg">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Crawl Success Rate</span>
            <span className="text-2xl font-extrabold text-blue-600 dark:text-blue-400 mt-1 block font-mono">{(metrics.crawl_success_rate * 100).toFixed(0)}%</span>
          </div>
          <div className="bg-white dark:bg-slate-900/90 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-lg">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Review Queue</span>
            <span className="text-2xl font-extrabold text-amber-600 dark:text-amber-400 mt-1 block font-mono">{metrics.review_queue_count}</span>
          </div>
        </div>
      )}

      {error && <Alert type="error">{error}</Alert>}

      {isLoading ? (
        <Skeleton className="h-64 rounded-3xl" />
      ) : (
        <div className="bg-white dark:bg-slate-900/90 rounded-3xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-xl">
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-100/90 dark:bg-slate-950/90 font-bold text-xs uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-500" />
            <span>Recent Discovery Runs</span>
          </div>
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/90 dark:bg-slate-950/90 text-slate-700 dark:text-slate-300 uppercase tracking-wider font-bold border-b border-slate-200 dark:border-slate-800 select-none">
              <tr>
                <th className="p-4">Run ID</th>
                <th className="p-4">Status</th>
                <th className="p-4">Pages Fetched</th>
                <th className="p-4">Discovered</th>
                <th className="p-4">Duplicates</th>
                <th className="p-4">Started At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800/80 text-slate-800 dark:text-slate-200 font-medium">
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400 dark:text-slate-500 italic">
                    No crawl runs recorded yet. Discovery scheduler active.
                  </td>
                </tr>
              ) : (
                runs.map((r) => (
                  <tr key={r.id} className="hover:bg-indigo-500/5 dark:hover:bg-slate-800/60 transition-colors">
                    <td className="p-4 font-mono text-xs text-slate-600 dark:text-slate-300">{r.id.substring(0, 8)}...</td>
                    <td className="p-4">
                      <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                        r.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/20' : 'bg-red-500/10 text-red-700 dark:text-red-300 border-red-500/20'
                      }`}>
                        {r.status}
                      </span>
                    </td>
                    <td className="p-4 font-mono">{r.pages_fetched}</td>
                    <td className="p-4 font-bold text-emerald-600 dark:text-emerald-400 font-mono">{r.opportunities_found}</td>
                    <td className="p-4 text-slate-500 dark:text-slate-400 font-mono">{r.duplicates_detected}</td>
                    <td className="p-4 text-xs font-mono text-slate-500 dark:text-slate-400">{r.started_at ? new Date(r.started_at).toLocaleString() : 'N/A'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
