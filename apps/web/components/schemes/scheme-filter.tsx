'use client';

import React from 'react';
import { useTranslation } from '@/lib/i18n';
import { Search } from 'lucide-react';

interface SchemeFilterProps {
  query: string;
  category: string;
  scope: string;
  onQueryChange: (q: string) => void;
  onCategoryChange: (cat: string) => void;
  onScopeChange: (scope: string) => void;
}

export function SchemeFilter({
  query,
  category,
  scope,
  onQueryChange,
  onCategoryChange,
  onScopeChange
}: SchemeFilterProps) {
  const { t } = useTranslation();

  return (
    <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-center gap-4">
      {/* Search Input */}
      <div className="relative w-full md:flex-1">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder={t.schemes.searchPlaceholder}
          className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
        />
      </div>

      {/* Category Dropdown */}
      <div className="w-full md:w-48">
        <select
          value={category}
          onChange={(e) => onCategoryChange(e.target.value)}
          className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white"
        >
          <option value="">{t.schemes.allCategories}</option>
          <option value="agriculture">Agriculture</option>
          <option value="education">Education</option>
          <option value="health">Health & Housing</option>
          <option value="welfare">Social Welfare</option>
          <option value="financial">Financial Assistance</option>
        </select>
      </div>

      {/* Scope Dropdown */}
      <div className="w-full md:w-48">
        <select
          value={scope}
          onChange={(e) => onScopeChange(e.target.value)}
          className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white"
        >
          <option value="">{t.schemes.allScopes}</option>
          <option value="central">{t.schemes.central}</option>
          <option value="state">{t.schemes.state}</option>
        </select>
      </div>
    </div>
  );
}
