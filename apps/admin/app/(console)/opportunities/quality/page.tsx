'use client';

import React, { useState, useEffect } from 'react';
import { getOpportunityQualityQueue } from '@/lib/api/opportunities';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert } from '@/components/ui/alert';
import { Sparkles, CheckCircle2, XCircle } from 'lucide-react';

export default function QualityReviewQueuePage() {
  const [items, setItems] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadQueue() {
      setIsLoading(true);
      try {
        const queue = await getOpportunityQualityQueue();
        setItems(queue);
      } catch (err: any) {
        setError(err.message || 'Failed to load quality review queue.');
      } finally {
        setIsLoading(false);
      }
    }
    loadQueue();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      <div className="bg-white dark:bg-slate-900/90 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl space-y-1">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-amber-500" />
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">Quality Control Review Queue</h1>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Review medium and low-confidence extractions before surfacing to citizens (threshold &lt; 0.75).
        </p>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {isLoading ? (
        <Skeleton className="h-64 rounded-3xl" />
      ) : items.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-slate-900/90 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 flex items-center justify-center mx-auto">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <p className="text-base font-extrabold text-slate-900 dark:text-white">Review Queue Empty</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
              All extracted opportunities meet high-confidence quality standards.
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-900/90 rounded-3xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-xl">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/90 dark:bg-slate-950/90 text-slate-700 dark:text-slate-300 uppercase tracking-wider font-bold border-b border-slate-200 dark:border-slate-800 select-none">
              <tr>
                <th className="p-4">Opportunity Title</th>
                <th className="p-4">Organization</th>
                <th className="p-4">Quality Score</th>
                <th className="p-4">Source</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800/80 text-slate-800 dark:text-slate-200 font-medium">
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-indigo-500/5 dark:hover:bg-slate-800/60 transition-colors">
                  <td className="p-4 font-bold text-slate-900 dark:text-white">{item.title}</td>
                  <td className="p-4 text-slate-600 dark:text-slate-400">{item.organization}</td>
                  <td className="p-4 font-bold text-amber-600 dark:text-amber-400 font-mono">{(item.quality_score * 100).toFixed(0)}%</td>
                  <td className="p-4 text-xs font-mono text-slate-500 dark:text-slate-400">{item.source_name}</td>
                  <td className="p-4 text-right space-x-2">
                    <button className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-sm">
                      Approve &amp; Publish
                    </button>
                    <button className="px-3 py-1.5 bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-xs rounded-xl hover:bg-slate-300">
                      Reject
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
