'use client';

import React, { useState, useEffect } from 'react';
import { getCrawlRuns, getCrawlMetrics, CrawlRun, CrawlMetrics } from '@/lib/api/opportunities';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert } from '@/components/ui/alert';

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
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900">Crawl Observability & Metrics</h1>
        <p className="text-sm text-slate-500 mt-1">
          Monitor 30-minute discovery scheduler execution logs, success rates, and items discovered.
        </p>
      </div>

      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <span className="text-xs text-slate-400 font-medium block uppercase">Active Sources</span>
            <span className="text-2xl font-extrabold text-slate-900 mt-1 block">{metrics.active_sources}</span>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <span className="text-xs text-slate-400 font-medium block uppercase">Verified Portals</span>
            <span className="text-2xl font-extrabold text-emerald-600 mt-1 block">{metrics.verified_sources}</span>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <span className="text-xs text-slate-400 font-medium block uppercase">Crawl Success Rate</span>
            <span className="text-2xl font-extrabold text-blue-600 mt-1 block">{(metrics.crawl_success_rate * 100).toFixed(0)}%</span>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <span className="text-xs text-slate-400 font-medium block uppercase">Review Queue</span>
            <span className="text-2xl font-extrabold text-amber-600 mt-1 block">{metrics.review_queue_count}</span>
          </div>
        </div>
      )}

      {error && <Alert type="error">{error}</Alert>}

      {isLoading ? (
        <Skeleton className="h-64 rounded-2xl" />
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="p-4 border-b border-slate-100 bg-slate-50 font-bold text-sm text-slate-800">
            Recent Discovery Runs
          </div>
          <table className="w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500 border-b border-slate-200">
              <tr>
                <th className="p-4">Run ID</th>
                <th className="p-4">Status</th>
                <th className="p-4">Pages Fetched</th>
                <th className="p-4">Discovered</th>
                <th className="p-4">Duplicates</th>
                <th className="p-4">Started At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {runs.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50/50">
                  <td className="p-4 font-mono text-xs text-slate-600">{r.id.substring(0, 8)}...</td>
                  <td className="p-4">
                    <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                      r.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {r.status}
                    </span>
                  </td>
                  <td className="p-4">{r.pages_fetched}</td>
                  <td className="p-4 font-bold text-emerald-600">{r.opportunities_found}</td>
                  <td className="p-4 text-slate-500">{r.duplicates_detected}</td>
                  <td className="p-4 text-xs text-slate-500">{r.started_at ? new Date(r.started_at).toLocaleString() : 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
