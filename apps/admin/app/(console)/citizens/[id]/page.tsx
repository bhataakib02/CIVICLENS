'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { CitizenProfileView } from '@/components/citizens/citizen-profile';
import { getCitizenDetail, getCitizenConsents } from '@/lib/api/citizens';
import { CitizenDetail } from '@/types/api';
import { ArrowLeft, Loader2, ShieldCheck } from 'lucide-react';
import Link from 'next/link';

export default function CitizenDetailPage() {
  const params = useParams();
  const userId = params.id as string;
  const [citizen, setCitizen] = useState<CitizenDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchDetail = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getCitizenDetail(userId);
      const consents = await getCitizenConsents(userId);
      setCitizen({ ...data, consents } as any);
    } catch (err: any) {
      setError(err.message || 'Failed to load citizen record.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userId) fetchDetail();
  }, [userId]);

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Link href="/citizens" className="btn-secondary text-xs p-2 rounded-xl border border-slate-200 dark:border-slate-800">
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-xl font-extrabold text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-indigo-500" />
            <span>Citizen Profile Record</span>
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">User UUID: {userId}</p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-semibold">
          {error}
        </div>
      )}

      {loading && !citizen ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
        </div>
      ) : citizen ? (
        <CitizenProfileView citizen={citizen} onRefresh={fetchDetail} />
      ) : null}
    </div>
  );
}
