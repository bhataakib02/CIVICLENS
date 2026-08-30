'use client';

import React, { useState, useEffect } from 'react';
import { getBrokenLinksReport } from '@/lib/api/opportunities';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert } from '@/components/ui/alert';
import { Link2, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function BrokenLinksMonitorPage() {
  const [links, setLinks] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadReport() {
      setIsLoading(true);
      try {
        const data = await getBrokenLinksReport();
        setLinks(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load broken links report.');
      } finally {
        setIsLoading(false);
      }
    }
    loadReport();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      <div className="bg-white dark:bg-slate-900/90 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl space-y-1">
        <div className="flex items-center gap-2">
          <Link2 className="w-5 h-5 text-indigo-500" />
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">Broken Link Monitor</h1>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Monitor application URLs returning HTTP 404, 500, or connection failures during link verification.
        </p>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {isLoading ? (
        <Skeleton className="h-64 rounded-3xl" />
      ) : links.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-slate-900/90 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 flex items-center justify-center mx-auto">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <p className="text-base font-extrabold text-slate-900 dark:text-white">No Broken Links Detected</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
              All verified official application URLs are reachable.
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-900/90 rounded-3xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-xl">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/90 dark:bg-slate-950/90 text-slate-700 dark:text-slate-300 uppercase tracking-wider font-bold border-b border-slate-200 dark:border-slate-800 select-none">
              <tr>
                <th className="p-4">Target URL</th>
                <th className="p-4">Domain</th>
                <th className="p-4">HTTP Status</th>
                <th className="p-4">Last Verified</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800/80 text-slate-800 dark:text-slate-200 font-medium">
              {links.map((link) => (
                <tr key={link.id} className="hover:bg-indigo-500/5 dark:hover:bg-slate-800/60 transition-colors">
                  <td className="p-4 font-mono text-xs text-red-600 dark:text-red-400 truncate max-w-xs">{link.url}</td>
                  <td className="p-4 text-slate-600 dark:text-slate-400 font-mono">{link.domain}</td>
                  <td className="p-4 font-bold text-red-600 dark:text-red-400 font-mono">{link.http_status || '404 / Failed'}</td>
                  <td className="p-4 text-xs font-mono text-slate-500 dark:text-slate-400">{link.verified_at ? new Date(link.verified_at).toLocaleString() : 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
