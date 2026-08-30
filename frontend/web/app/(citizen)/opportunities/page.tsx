'use client';

import React, { useState, useEffect } from 'react';
import { getOpportunities, Opportunity, OpportunityPage } from '@/lib/api/opportunities';
import { OpportunityFilter } from '@/components/opportunities/OpportunityFilter';
import { OpportunityCard } from '@/components/opportunities/OpportunityCard';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert } from '@/components/ui/alert';

export default function OpportunitiesPage() {
  const [data, setData] = useState<OpportunityPage | null>(null);
  const [query, setQuery] = useState('');
  const [type, setType] = useState('');
  const [location, setLocation] = useState('');
  const [isGovOnly, setIsGovOnly] = useState(false);
  const [closingSoon, setClosingSoon] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadOpportunities() {
      setIsLoading(true);
      setError(null);
      try {
        const res = await getOpportunities({
          q: query || undefined,
          type: type || undefined,
          location: location || undefined,
          is_government: isGovOnly ? true : undefined,
          closing_soon: closingSoon ? true : undefined,
          page: 1,
          page_size: 30,
        });
        setData(res);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch opportunities catalog.');
      } finally {
        setIsLoading(false);
      }
    }

    const timer = setTimeout(() => {
      loadOpportunities();
    }, 300);

    return () => clearTimeout(timer);
  }, [query, type, location, isGovOnly, closingSoon]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-800 to-emerald-950 text-white p-6 rounded-3xl shadow-md">
        <div>
          <span className="bg-emerald-500/20 text-emerald-300 text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full border border-emerald-500/30">
            Unified Discovery Engine
          </span>
          <h1 className="text-2xl md:text-3xl font-extrabold mt-2">Discover Public & Private Opportunities</h1>
          <p className="text-sm text-slate-300 mt-1 max-w-2xl">
            Explore verified government jobs, internships, scholarships, fellowships, and schemes from registered authoritative portals.
          </p>
        </div>

        {data && (
          <div className="flex flex-wrap md:flex-col gap-2 text-xs text-slate-300 border-t md:border-t-0 md:border-l border-slate-700 pt-3 md:pt-0 md:pl-6">
            <div>
              <span className="text-slate-400">Indexed Sources:</span> <strong className="text-white">{data.indexed_sources}</strong>
            </div>
            <div>
              <span className="text-slate-400">Verified Portals:</span> <strong className="text-emerald-400">{data.verified_sources}</strong>
            </div>
            <div>
              <span className="text-slate-400">Last Verified:</span>{' '}
              <strong className="text-white">
                {data.last_verification_time ? new Date(data.last_verification_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Just now'}
              </strong>
            </div>
          </div>
        )}
      </div>

      <OpportunityFilter
        query={query}
        type={type}
        location={location}
        isGovOnly={isGovOnly}
        closingSoon={closingSoon}
        onQueryChange={setQuery}
        onTypeChange={setType}
        onLocationChange={setLocation}
        onGovOnlyChange={setIsGovOnly}
        onClosingSoonChange={setClosingSoon}
      />

      {error && <Alert type="error">{error}</Alert>}

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Skeleton className="h-64 rounded-2xl" />
          <Skeleton className="h-64 rounded-2xl" />
          <Skeleton className="h-64 rounded-2xl" />
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <p className="text-4xl mb-2">🔍</p>
          <p className="text-slate-700 font-semibold text-base">No matching opportunities found</p>
          <p className="text-slate-500 text-xs mt-1">Try clearing your filters or refining your search terms.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.items.map((opp) => (
            <OpportunityCard key={opp.id} opportunity={opp} />
          ))}
        </div>
      )}
    </div>
  );
}
