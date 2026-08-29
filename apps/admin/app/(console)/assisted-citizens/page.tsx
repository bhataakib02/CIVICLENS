'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AssistedCitizenList } from '@/components/agents/assisted-citizen-list';
import { getAgentCitizens } from '@/lib/api/citizens';
import { AssistedCitizen } from '@/types/api';
import { UserCheck, Loader2 } from 'lucide-react';

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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-console-text tracking-tight">Agent / CSC Assisted Citizens</h1>
          <p className="text-xs text-console-muted mt-1">
            Authorized view of citizens who have granted active consent for agent assistance
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-console-accent" />
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
