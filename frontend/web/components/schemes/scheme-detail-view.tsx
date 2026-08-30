'use client';

import React, { useState } from 'react';
import { SchemeDetail, EligibilityResult } from '@/types/api';
import { checkEligibility } from '@/lib/api/eligibility';
import { createApplication } from '@/lib/api/applications';
import { useTranslation } from '@/lib/i18n';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/ui/status-badge';
import { Alert } from '@/components/ui/alert';
import {
  Building2,
  FileCheck,
  CheckCircle,
  ExternalLink,
  ShieldCheck,
  Sparkles,
  ArrowLeft
} from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface SchemeDetailViewProps {
  scheme: SchemeDetail;
}

export function SchemeDetailView({ scheme }: SchemeDetailViewProps) {
  const { t } = useTranslation();
  const router = useRouter();

  const [eligibility, setEligibility] = useState<EligibilityResult | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCheckEligibility = async () => {
    setIsChecking(true);
    setError(null);
    try {
      const res = await checkEligibility(scheme.id);
      setEligibility(res);
    } catch (err: any) {
      setError(err.message || 'Failed to check eligibility.');
    } finally {
      setIsChecking(false);
    }
  };

  const handleStartApplication = async () => {
    setIsApplying(true);
    setError(null);
    try {
      const app = await createApplication({
        scheme_id: scheme.id,
        scheme_version_id: scheme.scheme_version_id
      });
      router.push(`/applications/${app.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to start application.');
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div className="space-y-6">
      <Link href="/schemes">
        <Button variant="ghost" size="sm" className="mb-2">
          <ArrowLeft className="w-4 h-4 mr-1" />
          {t.common.back} {t.nav.schemes}
        </Button>
      </Link>

      {/* Header Banner */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className="text-xs font-bold px-2.5 py-1 rounded-md bg-blue-50 text-blue-800 uppercase tracking-wide">
            {scheme.scope === 'central' ? t.schemes.central : t.schemes.state}
          </span>
          <span className="text-xs font-medium px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 capitalize">
            {scheme.category}
          </span>
        </div>

        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 mb-2">
          {scheme.canonical_name}
        </h1>

        {scheme.administering_dept && (
          <p className="text-sm text-slate-500 flex items-center gap-1.5 mb-6">
            <Building2 className="w-4 h-4 text-slate-400" />
            <span>{t.schemes.department}: <strong className="text-slate-700">{scheme.administering_dept}</strong></span>
          </p>
        )}

        <div className="flex flex-wrap gap-4 pt-4 border-t border-slate-100">
          <Button onClick={handleCheckEligibility} isLoading={isChecking}>
            <CheckCircle className="w-4 h-4 mr-2" />
            {t.schemes.checkEligibilityForThis}
          </Button>

          {eligibility && (eligibility.result === 'eligible' || eligibility.result === 'likely_eligible') && (
            <Button variant="secondary" onClick={handleStartApplication} isLoading={isApplying}>
              {t.schemes.startApplication}
            </Button>
          )}
        </div>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {/* Eligibility Result Banner if checked */}
      {eligibility && (
        <Card className="border-l-4 border-l-blue-600 bg-blue-50/50">
          <CardHeader className="flex items-center justify-between">
            <CardTitle className="text-base font-bold text-slate-900">Your Eligibility Evaluation</CardTitle>
            <StatusBadge status={eligibility.result} />
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-700 mb-3">
              {eligibility.result === 'eligible' && t.eligibility.eligibleDesc}
              {eligibility.result === 'likely_eligible' && t.eligibility.likelyEligibleDesc}
              {eligibility.result === 'not_eligible' && t.eligibility.notEligibleDesc}
              {eligibility.result === 'insufficient_data' && t.eligibility.insufficientDataDesc}
            </p>
            <Link href="/eligibility">
              <Button size="sm" variant="outline">{t.eligibility.ruleBreakdown}</Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* Benefits & Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* CivicLens AI Explanation Box */}
          <Card>
            <CardHeader className="flex items-center gap-2 pb-2">
              <Sparkles className="w-5 h-5 text-blue-600" />
              <CardTitle className="text-base font-bold text-slate-900">{t.schemes.civicLensSummaryNotice}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-700 leading-relaxed">
                {scheme.benefits_summary}
              </p>
            </CardContent>
          </Card>

          {/* Required Documents Checklist */}
          <Card>
            <CardHeader className="flex items-center gap-2">
              <FileCheck className="w-5 h-5 text-slate-600" />
              <CardTitle className="text-base font-bold text-slate-900">{t.schemes.requiredDocs}</CardTitle>
            </CardHeader>
            <CardContent>
              {(!scheme.document_requirements || scheme.document_requirements.length === 0) ? (
                <p className="text-sm text-slate-500 italic">No document requirements explicitly declared.</p>
              ) : (
                <div className="space-y-3">
                  {scheme.document_requirements.map((doc, i) => (
                    <div key={i} className="flex items-start justify-between p-3 bg-slate-50 rounded-xl border border-slate-100">
                      <div>
                        <span className="font-semibold text-slate-900 text-sm capitalize">{doc.document_type}</span>
                        {doc.notes && <p className="text-xs text-slate-500 mt-0.5">{doc.notes}</p>}
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${doc.is_mandatory ? 'bg-red-50 text-red-700' : 'bg-slate-200 text-slate-600'}`}>
                        {doc.is_mandatory ? t.common.required : t.common.optional}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Official Source Metadata Side Box */}
        <div>
          <Card className="bg-slate-900 text-white">
            <CardHeader className="flex items-center gap-2 pb-3 border-b border-slate-800">
              <ShieldCheck className="w-5 h-5 text-blue-400" />
              <CardTitle className="text-sm font-bold text-white">{t.schemes.officialSourceNotice}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-xs text-slate-300">
              <div>
                <span className="text-slate-400 block mb-0.5">Administering Dept</span>
                <span className="font-medium text-white">{scheme.administering_dept || 'Central / State Ministry'}</span>
              </div>

              {scheme.last_verified_at && (
                <div>
                  <span className="text-slate-400 block mb-0.5">Last Verified Date</span>
                  <span className="font-medium text-white">{new Date(scheme.last_verified_at).toLocaleDateString()}</span>
                </div>
              )}

              {scheme.official_source_url && (
                <a
                  href={scheme.official_source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-blue-400 hover:text-blue-300 font-semibold underline pt-2"
                >
                  <span>Official Portal</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
