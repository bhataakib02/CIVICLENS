'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { SimulationPanel } from '@/components/schemes/simulation-panel';
import { getVersionRules } from '@/lib/api/schemes';
import { EligibilityRule } from '@/types/api';
import { ArrowLeft, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function SimulatePage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const schemeId = params.id as string;
  const versionId = searchParams.get('versionId') || '';

  const [rules, setRules] = useState<EligibilityRule[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadRules() {
      if (!versionId) return;
      setLoading(true);
      try {
        const r = await getVersionRules(versionId);
        setRules(r);
      } catch (err) {
        setRules([]);
      } finally {
        setLoading(false);
      }
    }
    loadRules();
  }, [versionId]);

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Link href={`/schemes/${schemeId}`} className="btn-secondary text-xs p-2">
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-console-text tracking-tight">Policy Simulation Console</h1>
          <p className="text-xs text-console-muted">Scheme ID: {schemeId} | Version ID: {versionId}</p>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-console-accent" />
        </div>
      ) : (
        <SimulationPanel versionId={versionId} draftRules={rules} />
      )}
    </div>
  );
}
