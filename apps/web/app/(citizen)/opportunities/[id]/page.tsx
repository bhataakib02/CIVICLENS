'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getOpportunityDetail, Opportunity } from '@/lib/api/opportunities';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert } from '@/components/ui/alert';
import { ApplyInterstitialModal } from '@/components/opportunities/ApplyInterstitialModal';
import { ApplicationTrackerModal } from '@/components/opportunities/ApplicationTrackerModal';

export default function OpportunityDetailPage() {
  const params = useParams();
  const router = useRouter();
  const oppId = params.id as string;

  const [opp, setOpp] = useState<Opportunity | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [showTrackerModal, setShowTrackerModal] = useState(false);

  useEffect(() => {
    async function loadDetail() {
      setIsLoading(true);
      setError(null);
      try {
        const detail = await getOpportunityDetail(oppId);
        setOpp(detail);
      } catch (err: any) {
        setError(err.message || 'Failed to load opportunity details.');
      } finally {
        setIsLoading(false);
      }
    }
    if (oppId) {
      loadDetail();
    }
  }, [oppId]);

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 py-6">
        <Skeleton className="h-48 rounded-3xl" />
        <Skeleton className="h-96 rounded-2xl" />
      </div>
    );
  }

  if (error || !opp) {
    return (
      <div className="max-w-4xl mx-auto py-12 space-y-4">
        <Alert type="error">{error || 'Opportunity not found.'}</Alert>
        <button onClick={() => router.push('/opportunities')} className="text-emerald-600 font-semibold text-sm hover:underline">
          &larr; Back to Opportunity Explorer
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-16">
      <button onClick={() => router.push('/opportunities')} className="text-slate-500 hover:text-slate-900 font-medium text-xs flex items-center gap-1">
        &larr; Back to Opportunity Explorer
      </button>

      {/* Header Banner */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 md:p-8 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
            {opp.type}
          </span>
          <span className="text-xs text-slate-500 font-medium">
            Last verified: {new Date(opp.last_verified_at).toLocaleDateString()}
          </span>
        </div>

        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900">{opp.title}</h1>
        <p className="text-base font-semibold text-slate-700">{opp.organization}</p>

        <div className="flex flex-wrap items-center gap-3 pt-2 text-xs font-medium text-slate-600">
          {opp.location && <span className="bg-slate-100 px-3 py-1.5 rounded-xl">📍 {opp.location}</span>}
          {opp.remote && <span className="bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded-xl">🌐 Remote Work Allowed</span>}
          {opp.stipend && <span className="bg-emerald-50 text-emerald-800 px-3 py-1.5 rounded-xl font-bold">💰 {opp.stipend}</span>}
          {opp.fee && <span className="bg-slate-100 px-3 py-1.5 rounded-xl">🏷️ Fee: {opp.fee}</span>}
        </div>

        <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-4">
          <div className="text-xs">
            <span className="text-slate-400 block font-medium uppercase text-[10px]">Verified Source</span>
            <span className="font-bold text-slate-800">{opp.source_name} ({opp.source_domain})</span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowTrackerModal(true)}
              className="px-4 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 font-bold text-xs rounded-xl transition-colors"
            >
              📌 Track Application
            </button>
            <button
              onClick={() => setShowApplyModal(true)}
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm rounded-xl transition-colors shadow-sm"
            >
              APPLY ON OFFICIAL WEBSITE &rarr;
            </button>
          </div>
        </div>
      </div>

      {/* Match Score Breakdown */}
      {opp.match_breakdown && (
        <div className="bg-gradient-to-r from-emerald-900 to-slate-900 text-white p-6 rounded-3xl shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold flex items-center gap-2">
              <span>🎯</span> Why this matches your profile
            </h2>
            <span className="text-2xl font-black text-emerald-400">{opp.match_breakdown.overall_score}%</span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2 text-xs">
            <div className="bg-white/10 p-2.5 rounded-xl backdrop-blur-sm">
              <span className="text-slate-300 block text-[10px]">Skill Match</span>
              <span className="font-bold text-emerald-300">{opp.match_breakdown.skill_match}%</span>
            </div>
            <div className="bg-white/10 p-2.5 rounded-xl backdrop-blur-sm">
              <span className="text-slate-300 block text-[10px]">Education</span>
              <span className="font-bold text-emerald-300">{opp.match_breakdown.education_match}%</span>
            </div>
            <div className="bg-white/10 p-2.5 rounded-xl backdrop-blur-sm">
              <span className="text-slate-300 block text-[10px]">Location</span>
              <span className="font-bold text-emerald-300">{opp.match_breakdown.location_match}%</span>
            </div>
            <div className="bg-white/10 p-2.5 rounded-xl backdrop-blur-sm">
              <span className="text-slate-300 block text-[10px]">Eligibility</span>
              <span className="font-bold text-emerald-300">{opp.match_breakdown.eligibility_match}%</span>
            </div>
          </div>

          {opp.match_breakdown.reasons.length > 0 && (
            <ul className="text-xs text-slate-200 list-disc list-inside space-y-1 pt-1">
              {opp.match_breakdown.reasons.map((r, idx) => (
                <li key={idx}>{r}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Main Grid Details */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Description & Eligibility */}
        <div className="md:col-span-2 space-y-6">
          <div className="bg-white p-6 rounded-3xl border border-slate-200 space-y-3 shadow-sm">
            <h3 className="text-base font-bold text-slate-900">Description</h3>
            <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">{opp.description}</p>
          </div>

          {opp.eligibility && opp.eligibility.length > 0 && (
            <div className="bg-white p-6 rounded-3xl border border-slate-200 space-y-3 shadow-sm">
              <h3 className="text-base font-bold text-slate-900">Eligibility Criteria</h3>
              <ul className="list-disc list-inside text-sm text-slate-700 space-y-1.5">
                {opp.eligibility.map((req, i) => (
                  <li key={i}>{req}</li>
                ))}
              </ul>
            </div>
          )}

          {opp.benefits && opp.benefits.length > 0 && (
            <div className="bg-white p-6 rounded-3xl border border-slate-200 space-y-3 shadow-sm">
              <h3 className="text-base font-bold text-slate-900">Benefits & Compensation</h3>
              <ul className="list-disc list-inside text-sm text-slate-700 space-y-1.5">
                {opp.benefits.map((b, i) => (
                  <li key={i}>{b}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Right Column: Important Dates & Links */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-3xl border border-slate-200 space-y-4 shadow-sm">
            <h3 className="text-base font-bold text-slate-900">Important Dates</h3>
            <div className="space-y-3 text-xs">
              {opp.application_open_date && (
                <div>
                  <span className="text-slate-400 font-medium block">Application Opens</span>
                  <span className="font-semibold text-slate-800">{new Date(opp.application_open_date).toLocaleDateString()}</span>
                </div>
              )}
              {opp.application_deadline && (
                <div>
                  <span className="text-slate-400 font-medium block">Application Deadline</span>
                  <span className="font-bold text-amber-700">{new Date(opp.application_deadline).toLocaleDateString()}</span>
                </div>
              )}
              {opp.event_date && (
                <div>
                  <span className="text-slate-400 font-medium block">Event / Exam Date</span>
                  <span className="font-semibold text-slate-800">{new Date(opp.event_date).toLocaleDateString()}</span>
                </div>
              )}
            </div>
          </div>

          <div className="bg-white p-6 rounded-3xl border border-slate-200 space-y-3 shadow-sm text-xs">
            <h3 className="text-base font-bold text-slate-900">Official Links</h3>
            <div className="space-y-2">
              <a
                href={opp.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-2.5 rounded-xl border border-slate-200 hover:border-emerald-500 font-medium text-slate-800 truncate"
              >
                📄 Official Notice Page &rarr;
              </a>
              {opp.application_url && (
                <a
                  href={opp.application_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block p-2.5 rounded-xl bg-emerald-50 border border-emerald-200 font-bold text-emerald-800 truncate"
                >
                  📝 Direct Apply Portal &rarr;
                </a>
              )}
            </div>
          </div>
        </div>
      </div>

      <ApplyInterstitialModal
        isOpen={showApplyModal}
        onClose={() => setShowApplyModal(false)}
        opportunity={opp}
      />

      <ApplicationTrackerModal
        isOpen={showTrackerModal}
        onClose={() => setShowTrackerModal(false)}
        opportunityId={opp.id}
        opportunityTitle={opp.title}
      />
    </div>
  );
}
