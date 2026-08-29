'use client';

import React, { useState, useEffect } from 'react';
import { getOpportunityQualityQueue } from '@/lib/api/opportunities';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert } from '@/components/ui/alert';

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
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900">Quality Control Review Queue</h1>
        <p className="text-sm text-slate-500 mt-1">
          Review medium and low-confidence extractions before surfacing to citizens (threshold &lt; 0.75).
        </p>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {isLoading ? (
        <Skeleton className="h-64 rounded-2xl" />
      ) : items.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <p className="text-3xl mb-2">🎉</p>
          <p className="text-slate-700 font-semibold text-sm">Review Queue Empty</p>
          <p className="text-slate-500 text-xs mt-1">All extracted opportunities meet high-confidence quality standards.</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
          <table className="w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500 border-b border-slate-200">
              <tr>
                <th className="p-4">Opportunity Title</th>
                <th className="p-4">Organization</th>
                <th className="p-4">Quality Score</th>
                <th className="p-4">Source</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50/50">
                  <td className="p-4 font-bold text-slate-900">{item.title}</td>
                  <td className="p-4 text-slate-600">{item.organization}</td>
                  <td className="p-4 font-bold text-amber-600">{(item.quality_score * 100).toFixed(0)}%</td>
                  <td className="p-4 text-xs text-slate-500">{item.source_name}</td>
                  <td className="p-4 text-right space-x-2">
                    <button className="px-3 py-1 bg-emerald-600 text-white font-semibold text-xs rounded-lg hover:bg-emerald-700">
                      Approve & Publish
                    </button>
                    <button className="px-3 py-1 bg-slate-200 text-slate-700 font-semibold text-xs rounded-lg hover:bg-slate-300">
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
