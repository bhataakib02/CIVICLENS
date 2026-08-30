'use client';

import React from 'react';
import { Input } from '@/components/ui/input';

interface OpportunityFilterProps {
  query: string;
  type: string;
  location: string;
  isGovOnly: boolean;
  closingSoon: boolean;
  onQueryChange: (v: string) => void;
  onTypeChange: (v: string) => void;
  onLocationChange: (v: string) => void;
  onGovOnlyChange: (v: boolean) => void;
  onClosingSoonChange: (v: boolean) => void;
  onSearchNaturalLanguage?: (q: string) => void;
}

export function OpportunityFilter({
  query,
  type,
  location,
  isGovOnly,
  closingSoon,
  onQueryChange,
  onTypeChange,
  onLocationChange,
  onGovOnlyChange,
  onClosingSoonChange,
}: OpportunityFilterProps) {
  const types = [
    { label: 'All Opportunities', value: '' },
    { label: 'Government Jobs', value: 'JOB' },
    { label: 'Internships', value: 'INTERNSHIP' },
    { label: 'Apprenticeships', value: 'APPRENTICESHIP' },
    { label: 'Scholarships', value: 'SCHOLARSHIP' },
    { label: 'Fellowships', value: 'FELLOWSHIP' },
    { label: 'Government Schemes', value: 'GOVERNMENT_SCHEME' },
    { label: 'Grants', value: 'GRANT' },
    { label: 'Training Programs', value: 'TRAINING' },
  ];

  return (
    <div className="bg-white p-4 rounded-2xl border border-slate-200 space-y-4 shadow-sm">
      <div className="flex flex-col md:flex-row gap-3">
        <div className="flex-1">
          <Input
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="🔍 Search opportunities by keyword, title, organization, or try natural language ('Find software internships in Bangalore')..."
            className="w-full"
          />
        </div>
        <div className="w-full md:w-48">
          <Input
            value={location}
            onChange={(e) => onLocationChange(e.target.value)}
            placeholder="📍 Location / City"
            className="w-full"
          />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap items-center gap-1.5 pt-1 overflow-x-auto border-t border-slate-100">
        {types.map((t) => (
          <button
            key={t.value}
            onClick={() => onTypeChange(t.value)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
              type === t.value
                ? 'bg-slate-900 text-white shadow-sm'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Checkboxes */}
      <div className="flex items-center gap-4 text-xs font-medium text-slate-700 pt-1">
        <label className="flex items-center gap-1.5 cursor-pointer">
          <input
            type="checkbox"
            checked={isGovOnly}
            onChange={(e) => onGovOnlyChange(e.target.checked)}
            className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
          />
          🏛️ Official Government Only
        </label>
        <label className="flex items-center gap-1.5 cursor-pointer">
          <input
            type="checkbox"
            checked={closingSoon}
            onChange={(e) => onClosingSoonChange(e.target.checked)}
            className="rounded border-slate-300 text-amber-600 focus:ring-amber-500"
          />
          ⏳ Closing Soon (within 5 days)
        </label>
      </div>
    </div>
  );
}
