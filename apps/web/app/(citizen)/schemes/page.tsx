'use client';

import React, { useState, useEffect } from 'react';
import { getSchemes } from '@/lib/api/schemes';
import { SchemeSummary } from '@/types/api';
import { SchemeFilter } from '@/components/schemes/scheme-filter';
import { SchemeCard } from '@/components/schemes/scheme-card';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert } from '@/components/ui/alert';
import { useTranslation } from '@/lib/i18n';

export default function SchemesPage() {
  const { t } = useTranslation();
  const [schemes, setSchemes] = useState<SchemeSummary[]>([]);
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [scope, setScope] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadSchemes() {
      setIsLoading(true);
      setError(null);
      try {
        const pageData = await getSchemes({
          q: query || undefined,
          category: category || undefined,
          scope: (scope as any) || undefined
        });
        setSchemes(pageData?.items || []);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch scheme catalog.');
      } finally {
        setIsLoading(false);
      }
    }

    const timer = setTimeout(() => {
      loadSchemes();
    }, 300);

    return () => clearTimeout(timer);
  }, [query, category, scope]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900">{t.schemes.title}</h1>
        <p className="text-sm text-slate-500 mt-1">{t.schemes.subtitle}</p>
      </div>

      <SchemeFilter
        query={query}
        category={category}
        scope={scope}
        onQueryChange={setQuery}
        onCategoryChange={setCategory}
        onScopeChange={setScope}
      />

      {error && <Alert type="error">{error}</Alert>}

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
      ) : schemes.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-2xl border border-slate-200">
          <p className="text-slate-500 text-sm">{t.common.noData}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {schemes.map((scheme) => (
            <SchemeCard key={scheme.id} scheme={scheme} />
          ))}
        </div>
      )}
    </div>
  );
}
