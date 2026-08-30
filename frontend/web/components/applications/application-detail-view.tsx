'use client';

import React, { useState, useEffect } from 'react';
import { getApplicationDetail, getApplicationChecklist, withdrawApplication, downloadApplicationPdf } from '@/lib/api/applications';
import { ApplicationDetail, ApplicationChecklist } from '@/types/api';
import { useTranslation } from '@/lib/i18n';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/ui/status-badge';
import { Timeline } from '@/components/ui/timeline';
import { Alert } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { SubmitConfirmationModal } from './submit-confirmation-modal';
import { formatDate } from '@/lib/formatting/date';
import { Download, CheckCircle2, AlertTriangle, FileText, ArrowLeft, Ban } from 'lucide-react';
import Link from 'next/link';

interface ApplicationDetailViewProps {
  applicationId: string;
}

export function ApplicationDetailView({ applicationId }: ApplicationDetailViewProps) {
  const { t } = useTranslation();
  const [detail, setDetail] = useState<ApplicationDetail | null>(null);
  const [checklist, setChecklist] = useState<ApplicationChecklist | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [isWithdrawing, setIsWithdrawing] = useState(false);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [appData, chkData] = await Promise.allSettled([
        getApplicationDetail(applicationId),
        getApplicationChecklist(applicationId)
      ]);

      if (appData.status === 'fulfilled') setDetail(appData.value);
      if (chkData.status === 'fulfilled') setChecklist(chkData.value);
    } catch (err: any) {
      setError(err.message || 'Failed to load application details.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [applicationId]);

  const handleDownloadPdf = async () => {
    setIsExporting(true);
    try {
      const blob = await downloadApplicationPdf(applicationId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Application-${applicationId.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err: any) {
      setError(err.message || 'Failed to export application package PDF.');
    } finally {
      setIsExporting(false);
    }
  };

  const handleWithdraw = async () => {
    if (!confirm('Are you sure you want to withdraw this application?')) return;
    setIsWithdrawing(true);
    try {
      await withdrawApplication(applicationId);
      await fetchData();
    } catch (err: any) {
      setError(err.message || 'Failed to withdraw application.');
    } finally {
      setIsWithdrawing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (!detail) {
    return (
      <Alert type="error" title="Application Not Found">
        Could not retrieve application details.
      </Alert>
    );
  }

  const timelineItems = (detail.status_history || []).map((h, i) => ({
    id: i.toString(),
    status: h.to_status,
    note: h.note,
    timestamp: h.created_at
  }));

  const canSubmit = detail.status === 'draft' || detail.status === 'ready_for_submission';
  const canWithdraw = detail.status !== 'approved' && detail.status !== 'rejected' && detail.status !== 'withdrawn' && detail.status !== 'completed';

  return (
    <div className="space-y-6">
      <Link href="/applications">
        <Button variant="ghost" size="sm" className="mb-2">
          <ArrowLeft className="w-4 h-4 mr-1" />
          {t.common.back} {t.nav.applications}
        </Button>
      </Link>

      {/* Header Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs text-slate-400 font-mono block mb-1">
            Application ID: {detail.id}
          </span>
          <h1 className="text-2xl font-extrabold text-slate-900">
            {detail.scheme_name || `Application #${detail.id.slice(0, 8)}`}
          </h1>
          <p className="text-xs text-slate-500 mt-1">Created: {formatDate(detail.created_at)}</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge status={detail.status} />
          <Button variant="outline" size="sm" onClick={handleDownloadPdf} isLoading={isExporting}>
            <Download className="w-3.5 h-3.5 mr-1" />
            PDF
          </Button>

          {canSubmit && (
            <Button size="sm" onClick={() => setIsSubmitModalOpen(true)}>
              {t.applications.submitAppBtn}
            </Button>
          )}

          {canWithdraw && (
            <Button size="sm" variant="danger" onClick={handleWithdraw} isLoading={isWithdrawing}>
              <Ban className="w-3.5 h-3.5 mr-1" />
              {t.applications.withdrawApp}
            </Button>
          )}
        </div>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Document Checklist & Attached Files */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="flex items-center justify-between">
              <CardTitle className="text-base font-bold">{t.applications.checklist}</CardTitle>
              {checklist?.all_required_satisfied ? (
                <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Ready
                </span>
              ) : (
                <span className="text-xs font-semibold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-full flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Incomplete
                </span>
              )}
            </CardHeader>
            <CardContent className="space-y-3">
              {(!checklist?.items || checklist.items.length === 0) ? (
                <p className="text-xs text-slate-500 italic">No document requirements linked.</p>
              ) : (
                checklist.items.map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3.5 bg-slate-50 rounded-xl border border-slate-100">
                    <div className="flex items-center gap-3">
                      {item.is_satisfied ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                      ) : (
                        <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0" />
                      )}
                      <div>
                        <span className="font-semibold text-slate-900 text-sm capitalize">{item.document_type.replace(/_/g, ' ')}</span>
                        {item.is_mandatory && <span className="text-xs text-red-600 ml-2">({t.common.required})</span>}
                      </div>
                    </div>

                    <div>
                      {item.is_satisfied ? (
                        <span className="text-xs text-emerald-700 font-semibold">{t.common.success}</span>
                      ) : (
                        <Link href="/documents">
                          <Button size="sm" variant="outline">{t.common.upload}</Button>
                        </Link>
                      )}
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* Attached Documents */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold">Attached Documents</CardTitle>
            </CardHeader>
            <CardContent>
              {(!detail.attached_documents || detail.attached_documents.length === 0) ? (
                <p className="text-xs text-slate-500 italic">No files attached to application package.</p>
              ) : (
                <div className="space-y-2">
                  {detail.attached_documents.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between p-3 bg-white border border-slate-200 rounded-xl text-xs">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-blue-600" />
                        <span className="font-semibold capitalize text-slate-800">{doc.document_type}</span>
                      </div>
                      <StatusBadge status={doc.status} />
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Status History Timeline Side Card */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold">{t.applications.timeline}</CardTitle>
            </CardHeader>
            <CardContent>
              <Timeline items={timelineItems} />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Submission Confirmation Modal */}
      {isSubmitModalOpen && detail && (
        <SubmitConfirmationModal
          isOpen={isSubmitModalOpen}
          onClose={() => setIsSubmitModalOpen(false)}
          applicationDetail={detail}
          onSubmitted={fetchData}
        />
      )}
    </div>
  );
}
