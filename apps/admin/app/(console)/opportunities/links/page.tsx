'use client';

import React, { useState, useEffect } from 'react';
import { getBrokenLinksReport } from '@/lib/api/opportunities';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert } from '@/components/ui/alert';

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
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900">Broken Link Monitor</h1>
        <p className="text-sm text-slate-500 mt-1">
          Monitor application URLs returning HTTP 404, 500, or connection failures during link verification.
        </p>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {isLoading ? (
        <Skeleton className="h-64 rounded-2xl" />
      ) : links.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <p className="text-3xl mb-2">✅</p>
          <p className="text-slate-700 font-semibold text-sm">No Broken Links Detected</p>
          <p className="text-slate-500 text-xs mt-1">All verified official application URLs are reachable.</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
          <table className="w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500 border-b border-slate-200">
              <tr>
                <th className="p-4">Target URL</th>
                <th className="p-4">Domain</th>
                <th className="p-4">HTTP Status</th>
                <th className="p-4">Last Verified</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {links.map((link) => (
                <tr key={link.id} className="hover:bg-slate-50/50">
                  <td className="p-4 font-mono text-xs text-red-600 truncate max-w-xs">{link.url}</td>
                  <td className="p-4 text-slate-600">{link.domain}</td>
                  <td className="p-4 font-bold text-red-600">{link.http_status || '404 / Failed'}</td>
                  <td className="p-4 text-xs text-slate-500">{link.verified_at ? new Date(link.verified_at).toLocaleString() : 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
