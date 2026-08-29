'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth/auth-context';
import { useTranslation } from '@/lib/i18n';
import { checkAllEligibility } from '@/lib/api/eligibility';
import { getApplications } from '@/lib/api/applications';
import { getDocuments } from '@/lib/api/documents';
import { getNotifications } from '@/lib/api/notifications';
import { EligibilityResult, Application, Document, Notification } from '@/types/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { StatusBadge } from '@/components/ui/status-badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert } from '@/components/ui/alert';
import {
  CheckCircle2,
  AlertTriangle,
  FileText,
  Bell,
  ArrowRight,
  UserCheck,
  FolderOpen,
  Sparkles
} from 'lucide-react';

export function DashboardView() {
  const { user } = useAuth();
  const { t } = useTranslation();

  const [eligibilityResults, setEligibilityResults] = useState<EligibilityResult[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboardData() {
      setIsLoading(true);
      try {
        const [eligData, appData, docData, notifData] = await Promise.allSettled([
          checkAllEligibility(),
          getApplications(),
          getDocuments(),
          getNotifications()
        ]);

        if (eligData.status === 'fulfilled') setEligibilityResults(eligData.value || []);
        if (appData.status === 'fulfilled') setApplications(appData.value?.items || []);
        if (docData.status === 'fulfilled') setDocuments(docData.value || []);
        if (notifData.status === 'fulfilled') setNotifications(notifData.value || []);
      } catch (err: any) {
        setError(err.message || 'Failed to load dashboard metrics.');
      } finally {
        setIsLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  const eligibleCount = eligibilityResults.filter((e) => e.result === 'eligible').length;
  const likelyEligibleCount = eligibilityResults.filter((e) => e.result === 'likely_eligible').length;

  const docsNeedingAction = documents.filter(
    (d) => d.status === 'verification_required' || d.status === 'uploaded' || d.status === 'processing'
  );

  const appsNeedingAction = applications.filter(
    (a) => a.status === 'action_required' || a.status === 'info_requested'
  );

  const unreadNotifsCount = notifications.filter((n) => !n.is_read).length;

  const profileCompletenessPct = Math.round((user?.profile_completeness || 0) * 100);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-28 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-blue-900 to-indigo-800 text-white rounded-2xl p-6 sm:p-8 shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold">{t.dashboard.welcomeTitle}</h1>
          <p className="text-blue-100 text-sm mt-1">
            Access your government schemes, document verifications, and active applications in one place.
          </p>
        </div>

        {/* Profile Completeness Gauge */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 flex items-center gap-4 border border-white/20">
          <div className="text-center">
            <span className="text-xs font-semibold text-blue-200 block">{t.dashboard.profileCompleteness}</span>
            <span className="text-2xl font-bold">{profileCompletenessPct}%</span>
          </div>
          {profileCompletenessPct < 100 && (
            <Link href="/profile">
              <Button size="sm" variant="outline" className="bg-white text-blue-900 border-none hover:bg-blue-50">
                <UserCheck className="w-4 h-4 mr-1" />
                {t.common.edit}
              </Button>
            </Link>
          )}
        </div>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {/* Action Required Priority Banner */}
      {(appsNeedingAction.length > 0 || docsNeedingAction.length > 0) && (
        <Alert type="warning" title={t.dashboard.actionRequired}>
          <div className="space-y-2 mt-1">
            {appsNeedingAction.map((app) => (
              <div key={app.id} className="flex items-center justify-between gap-2">
                <span>Application #{app.id.slice(0, 8)} requires your attention.</span>
                <Link href={`/applications/${app.id}`}>
                  <Button size="sm" variant="outline">{t.common.viewDetails}</Button>
                </Link>
              </div>
            ))}
            {docsNeedingAction.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between gap-2">
                <span>Document ({doc.document_type}) needs extraction verification.</span>
                <Link href="/documents">
                  <Button size="sm" variant="outline">{t.common.viewDetails}</Button>
                </Link>
              </div>
            ))}
          </div>
        </Alert>
      )}

      {/* Key Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <Card className="border-l-4 border-l-emerald-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">{t.dashboard.eligibleSchemes}</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{eligibleCount}</h3>
            </div>
            <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
              <CheckCircle2 className="w-6 h-6" />
            </div>
          </div>
          <Link href="/eligibility" className="text-xs text-blue-600 hover:underline mt-3 inline-flex items-center gap-1 font-semibold">
            {t.dashboard.checkEligibility} <ArrowRight className="w-3 h-3" />
          </Link>
        </Card>

        <Card className="border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">{t.dashboard.likelyEligibleSchemes}</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{likelyEligibleCount}</h3>
            </div>
            <div className="p-3 bg-amber-50 text-amber-600 rounded-xl">
              <AlertTriangle className="w-6 h-6" />
            </div>
          </div>
          <Link href="/eligibility" className="text-xs text-blue-600 hover:underline mt-3 inline-flex items-center gap-1 font-semibold">
            {t.common.viewDetails} <ArrowRight className="w-3 h-3" />
          </Link>
        </Card>

        <Card className="border-l-4 border-l-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">{t.dashboard.activeApplications}</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{applications.length}</h3>
            </div>
            <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
              <FolderOpen className="w-6 h-6" />
            </div>
          </div>
          <Link href="/applications" className="text-xs text-blue-600 hover:underline mt-3 inline-flex items-center gap-1 font-semibold">
            {t.nav.applications} <ArrowRight className="w-3 h-3" />
          </Link>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500">{t.dashboard.unreadNotifications}</p>
              <h3 className="text-2xl font-bold text-slate-900 mt-1">{unreadNotifsCount}</h3>
            </div>
            <div className="p-3 bg-purple-50 text-purple-600 rounded-xl">
              <Bell className="w-6 h-6" />
            </div>
          </div>
          <Link href="/notifications" className="text-xs text-blue-600 hover:underline mt-3 inline-flex items-center gap-1 font-semibold">
            {t.nav.notifications} <ArrowRight className="w-3 h-3" />
          </Link>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Active Applications */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex items-center justify-between">
            <CardTitle>{t.dashboard.activeApplications}</CardTitle>
            <Link href="/applications">
              <Button size="sm" variant="ghost">{t.common.viewDetails}</Button>
            </Link>
          </CardHeader>
          <CardContent>
            {applications.length === 0 ? (
              <div className="text-center py-8">
                <FolderOpen className="w-12 h-12 text-slate-300 mx-auto mb-2" />
                <p className="text-sm text-slate-500">{t.dashboard.noActiveApplications}</p>
                <Link href="/schemes" className="inline-block mt-4">
                  <Button size="sm">{t.dashboard.exploreSchemes}</Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {applications.slice(0, 5).map((app) => (
                  <div key={app.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-100">
                    <div>
                      <h4 className="font-semibold text-slate-900 text-sm">Application #{app.id.slice(0, 8)}</h4>
                      <p className="text-xs text-slate-500 mt-0.5">Created: {new Date(app.created_at).toLocaleDateString()}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <StatusBadge status={app.status} />
                      <Link href={`/applications/${app.id}`}>
                        <Button size="sm" variant="outline">{t.common.viewDetails}</Button>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Assistant Callout */}
        <Card className="bg-gradient-to-br from-slate-900 to-blue-950 text-white border-none flex flex-col justify-between">
          <div>
            <div className="w-10 h-10 bg-blue-500/20 rounded-xl flex items-center justify-center mb-4">
              <Sparkles className="w-6 h-6 text-blue-400" />
            </div>
            <h3 className="text-lg font-bold">{t.assistant.title}</h3>
            <p className="text-xs text-slate-300 mt-2 leading-relaxed">
              Have questions about eligibility criteria, document requirements, or government guidelines? Ask CivicLens Assistant for citations and advice.
            </p>
          </div>
          <Link href="/assistant" className="mt-6">
            <Button className="w-full bg-blue-600 hover:bg-blue-500 text-white">
              {t.nav.assistant} <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        </Card>
      </div>
    </div>
  );
}
