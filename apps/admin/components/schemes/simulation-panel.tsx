'use client';

import React, { useState } from 'react';
import { simulateRules } from '@/lib/api/schemes';
import { SimulationResult } from '@/types/api';
import { MetricCard } from '@/components/ui/metric-card';
import { Play, CheckCircle2, XCircle, MinusCircle, HelpCircle, Loader2 } from 'lucide-react';

interface SimulationPanelProps {
  versionId: string;
  draftRules: any[];
}

export function SimulationPanel({ versionId, draftRules }: SimulationPanelProps) {
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRunSimulation = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await simulateRules(versionId, draftRules);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Simulation failed to complete.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card p-6 space-y-6">
      <div className="flex items-center justify-between border-b border-console-border pb-4">
        <div>
          <h2 className="text-base font-bold text-console-text">Flagship Policy Simulation Engine</h2>
          <p className="text-xs text-console-muted mt-0.5">
            Simulate proposed draft rules against anonymized population profile datasets prior to publishing
          </p>
        </div>
        <button
          onClick={handleRunSimulation}
          disabled={loading || draftRules.length === 0}
          className="btn-primary text-xs bg-indigo-600 hover:bg-indigo-500 flex items-center space-x-2"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4 fill-current" />}
          <span>Run Policy Simulation</span>
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
          {error}
        </div>
      )}

      {result ? (
        <div className="space-y-6 animate-in fade-in duration-300">
          <div className="p-3 rounded-lg bg-console-bg border border-console-border text-xs text-console-muted flex justify-between font-mono">
            <span>Evaluated Sample Size: {result.total_profiles_evaluated} Anonymized Citizen Profiles</span>
            <span>PII Status: 100% Anonymized & Aggregated</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Newly Eligible"
              value={result.newly_eligible}
              subtitle="Citizens newly gaining eligibility under proposed rule"
              icon={CheckCircle2}
              variant="success"
            />
            <MetricCard
              title="Newly Ineligible"
              value={result.newly_ineligible}
              subtitle="Citizens losing eligibility under proposed rule"
              icon={XCircle}
              variant="danger"
            />
            <MetricCard
              title="Unchanged Impact"
              value={result.unchanged}
              subtitle="Citizens whose eligibility status remains unchanged"
              icon={MinusCircle}
              variant="neutral"
            />
            <MetricCard
              title="Insufficient Data"
              value={result.insufficient_data}
              subtitle="Profiles lacking required facts for rule evaluation"
              icon={HelpCircle}
              variant="warning"
            />
          </div>
        </div>
      ) : (
        <p className="text-xs text-console-muted italic text-center py-8">
          Click &quot;Run Policy Simulation&quot; to evaluate draft rule outcomes against backend population datasets.
        </p>
      )}
    </div>
  );
}
