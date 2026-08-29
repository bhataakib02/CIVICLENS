'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Opportunity } from '@/lib/api/opportunities';
import { ApplyInterstitialModal } from './ApplyInterstitialModal';
import { ApplicationTrackerModal } from './ApplicationTrackerModal';

interface OpportunityCardProps {
  opportunity: Opportunity;
}

export function OpportunityCard({ opportunity }: OpportunityCardProps) {
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [showTrackerModal, setShowTrackerModal] = useState(false);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'CLOSING_SOON':
        return <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-200">⏳ Closing Soon</span>;
      case 'OPEN':
        return <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-200">🟢 Open</span>;
      case 'UPCOMING':
        return <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-blue-200">📅 Upcoming</span>;
      case 'CLOSED':
        return <span className="bg-slate-100 text-slate-600 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-slate-200">🔴 Closed</span>;
      default:
        return <span className="bg-slate-100 text-slate-700 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-slate-200">ℹ️ Notice</span>;
    }
  };

  const getAuthorityBadge = (domain: string, sourceType: string) => {
    const isGov = sourceType.includes('GOVERNMENT') || domain.endsWith('.gov.in') || domain.endsWith('.nic.in');
    if (isGov) {
      return <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">Official Government ✓</span>;
    }
    return <span className="text-[11px] font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">Verified Private Source</span>;
  };

  return (
    <>
      <div className="bg-white rounded-2xl border border-slate-200 p-5 hover:shadow-md transition-shadow flex flex-col justify-between space-y-4">
        <div>
          <div className="flex items-center justify-between gap-2 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-600 bg-emerald-50 px-2.5 py-0.5 rounded-md">
              {opportunity.type}
            </span>
            {getStatusBadge(opportunity.status)}
          </div>

          <Link href={`/opportunities/${opportunity.id}`} className="group">
            <h3 className="text-lg font-bold text-slate-900 group-hover:text-emerald-600 transition-colors line-clamp-2">
              {opportunity.title}
            </h3>
          </Link>

          <p className="text-sm font-semibold text-slate-700 mt-1">{opportunity.organization}</p>

          <div className="flex flex-wrap items-center gap-2 mt-3 text-xs text-slate-500">
            {opportunity.location && (
              <span className="flex items-center gap-1 bg-slate-50 px-2 py-1 rounded border border-slate-100">
                📍 {opportunity.location}
              </span>
            )}
            {opportunity.remote && (
              <span className="flex items-center gap-1 bg-indigo-50 text-indigo-700 px-2 py-1 rounded border border-indigo-100 font-medium">
                🌐 Remote Available
              </span>
            )}
            {opportunity.stipend && (
              <span className="flex items-center gap-1 bg-emerald-50 text-emerald-800 px-2 py-1 rounded border border-emerald-100 font-semibold">
                💰 {opportunity.stipend}
              </span>
            )}
          </div>

          {opportunity.summary && (
            <p className="text-xs text-slate-600 mt-3 line-clamp-2 leading-relaxed">
              {opportunity.summary}
            </p>
          )}

          {opportunity.match_breakdown && (
            <div className="mt-3 p-2.5 bg-slate-50 rounded-xl border border-slate-100">
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="font-semibold text-slate-700">Profile Match</span>
                <span className="font-bold text-emerald-600">{opportunity.match_breakdown.overall_score}%</span>
              </div>
              <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-emerald-500 h-full rounded-full"
                  style={{ width: `${opportunity.match_breakdown.overall_score}%` }}
                />
              </div>
            </div>
          )}
        </div>

        <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
          <div>
            {getAuthorityBadge(opportunity.source_domain, opportunity.source_type)}
            <p className="text-[10px] text-slate-400 mt-1">Verified: {new Date(opportunity.last_verified_at).toLocaleDateString()}</p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowTrackerModal(true)}
              title="Track Application Status"
              className="p-2 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors"
            >
              📌
            </button>
            <button
              onClick={() => setShowApplyModal(true)}
              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl transition-colors shadow-sm"
            >
              APPLY ON OFFICIAL SITE &rarr;
            </button>
          </div>
        </div>
      </div>

      <ApplyInterstitialModal
        isOpen={showApplyModal}
        onClose={() => setShowApplyModal(false)}
        opportunity={opportunity}
      />

      <ApplicationTrackerModal
        isOpen={showTrackerModal}
        onClose={() => setShowTrackerModal(false)}
        opportunityId={opportunity.id}
        opportunityTitle={opportunity.title}
      />
    </>
  );
}
