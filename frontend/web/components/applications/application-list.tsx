'use client';

import React, { useState, useEffect } from 'react';
import { getApplications } from '@/lib/api/applications';
import { Application } from '@/types/api';
import { useTranslation } from '@/lib/i18n';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/ui/status-badge';
import { Alert } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { formatDate } from '@/lib/formatting/date';
import { FolderOpen, Plus, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export function ApplicationList() {
  const { t } = useTranslation();
  const [applications, setApplications] = useState<Application[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchApps = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const pageData = await getApplications();
      setApplications(pageData?.items || []);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch applications.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchApps();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900">{t.applications.title}</h1>
          <p className="text-sm text-slate-500 mt-1">{t.applications.subtitle}</p>
        </div>
        <Link href="/schemes">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            {t.applications.newApp}
          </Button>
        </Link>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
      ) : applications.length === 0 ? (
        <Card className="text-center py-12">
          <FolderOpen className="w-12 h-12 text-slate-300 mx-auto mb-2" />
          <p className="text-slate-500 text-sm">{t.dashboard.noActiveApplications}</p>
          <Link href="/schemes" className="inline-block mt-4">
            <Button size="sm">{t.dashboard.exploreSchemes}</Button>
          </Link>
        </Card>
      ) : (
        <div className="space-y-4">
          {applications.map((app) => (
            <Card key={app.id} className="hover:border-blue-200 transition-colors p-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <span className="text-xs text-slate-400 font-mono block mb-0.5">
                    ID: {app.id.slice(0, 8)}
                  </span>
                  <h4 className="font-bold text-slate-900 text-base">
                    {app.scheme_name || `Scheme Application #${app.id.slice(0, 8)}`}
                  </h4>
                  <p className="text-xs text-slate-500 mt-1">
                    {t.applications.submittedAt}: {app.submitted_at ? formatDate(app.submitted_at) : 'Not Submitted'}
                  </p>
                </div>

                <div className="flex items-center gap-4 justify-between sm:justify-end">
                  <StatusBadge status={app.status} />
                  <Link href={`/applications/${app.id}`}>
                    <Button variant="outline" size="sm">
                      {t.common.viewDetails} <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </Link>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
