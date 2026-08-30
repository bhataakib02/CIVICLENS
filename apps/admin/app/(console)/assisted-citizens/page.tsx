'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AssistedCitizenList } from '@/components/agents/assisted-citizen-list';
import { getAgentCitizens } from '@/lib/api/citizens';
import { AssistedCitizen } from '@/types/api';
import { UserCheck, Loader2, ShieldCheck } from 'lucide-react';

export default function AssistedCitizensPage() {
  const router = useRouter();
  const [citizens, setCitizens] = useState<AssistedCitizen[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchAssisted = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getAgentCitizens();
      setCitizens(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load authorized citizens.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssisted();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      <div className="bg-white dark:bg-slate-900/90 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl space-y-1">
        <div className="flex items-center gap-2">
          <UserCheck className="w-5 h-5 text-indigo-500" />
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">Agent / CSC Assisted Citizens</h1>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Authorized view of citizens who have granted active consent for agent assistance.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-semibold">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center h-64 bg-white dark:bg-slate-900/90 rounded-3xl border border-slate-200 dark:border-slate-800">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
        </div>
      ) : (
        <AssistedCitizenList
          citizens={citizens}
          onSelect={(c) => {
            if (c.user_id) {
              router.push(`/citizens/${c.user_id}`);
            }
          }}
        />
      )}
    </div>
  );
}
