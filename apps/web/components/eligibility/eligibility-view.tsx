'use client';

import React, { useState, useEffect } from 'react';
import { checkAllEligibility } from '@/lib/api/eligibility';
import { EligibilityResult } from '@/types/api';
import { useTranslation } from '@/lib/i18n';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/ui/status-badge';
import { RuleBreakdownTable } from './rule-breakdown-table';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert } from '@/components/ui/alert';
import { CheckSquare, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export function EligibilityView() {
  const { t } = useTranslation();
  const [results, setResults] = useState<EligibilityResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEligibility = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await checkAllEligibility();
      setResults(res || []);
    } catch (err: any) {
      setError(err.message || 'Failed to evaluate scheme eligibility.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEligibility();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900">{t.eligibility.title}</h1>
          <p className="text-sm text-slate-500 mt-1">{t.eligibility.subtitle}</p>
        </div>
        <Button onClick={fetchEligibility} isLoading={isLoading}>
          <CheckSquare className="w-4 h-4 mr-2" />
          {t.eligibility.checkAllBtn}
        </Button>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
      ) : results.length === 0 ? (
        <Card className="text-center py-12">
          <p className="text-slate-500">{t.common.noData}</p>
        </Card>
      ) : (
        <div className="space-y-6">
          {results.map((res, idx) => (
            <Card key={res.scheme_id || idx} className="border-l-4 border-l-blue-600">
              <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <span className="text-xs font-semibold text-slate-400 block mb-1">
                    Scheme ID: {res.scheme_id.slice(0, 8)}
                  </span>
                  <CardTitle className="text-lg font-bold">
                    {res.scheme_name || `Scheme #${res.scheme_id.slice(0, 8)}`}
                  </CardTitle>
                </div>
                <StatusBadge status={res.result} />
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-slate-700">
                  {res.result === 'eligible' && t.eligibility.eligibleDesc}
                  {res.result === 'likely_eligible' && t.eligibility.likelyEligibleDesc}
                  {res.result === 'not_eligible' && t.eligibility.notEligibleDesc}
                  {res.result === 'insufficient_data' && t.eligibility.insufficientDataDesc}
                </p>

                {res.rule_breakdown && res.rule_breakdown.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">
                      {t.eligibility.ruleBreakdown}
                    </h4>
                    <RuleBreakdownTable rules={res.rule_breakdown} />
                  </div>
                )}

                <div className="pt-2 flex justify-end">
                  <Link href={`/schemes/${res.scheme_id}`}>
                    <Button size="sm" variant="outline">
                      {t.schemes.startApplication} <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
