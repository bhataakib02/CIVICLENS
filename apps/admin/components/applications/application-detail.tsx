import React from 'react';
import { ApplicationDetail as ApplicationDetailType } from '@/types/api';
import { StatusBadge } from '@/components/ui/status-badge';
import { Timeline } from '@/components/ui/timeline';
import { ReviewActions } from './review-actions';
import { formatDate, formatDateTime } from '@/lib/formatting';
import { FileText, Download, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { exportApplicationPdf } from '@/lib/api/applications';

interface ApplicationDetailProps {
  application: ApplicationDetailType;
  onRefresh: () => void;
}

export function ApplicationDetailView({ application, onRefresh }: ApplicationDetailProps) {
  const handleExportPdf = async () => {
    try {
      const blob = await exportApplicationPdf(application.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `application_${application.application_number}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert('Failed to export PDF package.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="glass-card p-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h2 className="text-lg font-bold font-mono text-console-accent">{application.application_number}</h2>
            <StatusBadge status={application.status} />
          </div>
          <p className="text-xs text-console-muted mt-1">
            Submitted: {formatDate(application.submitted_at)} | Scheme Version ID: {application.scheme_version_id}
          </p>
        </div>

        <button onClick={handleExportPdf} className="btn-secondary text-xs flex items-center space-x-2">
          <Download className="h-4 w-4" />
          <span>Export Case Package (PDF)</span>
        </button>
      </div>

      {/* Review Actions */}
      <ReviewActions application={application} onRefresh={onRefresh} />

      {/* Grid Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Eligibility Snapshot & Checklist */}
        <div className="lg:col-span-2 space-y-6">
          {/* Eligibility Engine Decision */}
          <div className="glass-card p-5">
            <h3 className="text-xs font-semibold text-console-muted uppercase tracking-wider mb-3">
              Authoritative Eligibility Snapshot
            </h3>
            {application.eligibility ? (
              <div className="p-4 rounded-lg bg-console-bg border border-console-border space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-console-muted">Engine Decision:</span>
                  <StatusBadge status={application.eligibility.decision || 'unknown'} />
                </div>
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-console-muted">Engine Version:</span>
                  <span className="text-console-text">{application.eligibility.engine_version || 'v1.0.0'}</span>
                </div>
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-console-muted">Evaluated At:</span>
                  <span className="text-console-text">{formatDateTime(application.eligibility.evaluated_at)}</span>
                </div>
              </div>
            ) : (
              <p className="text-xs text-console-muted italic">No eligibility evaluation snapshot attached.</p>
            )}
          </div>

          {/* Document Checklist */}
          <div className="glass-card p-5">
            <h3 className="text-xs font-semibold text-console-muted uppercase tracking-wider mb-3">
              Document Readiness Checklist
            </h3>
            {application.checklist?.items?.length > 0 ? (
              <div className="divide-y divide-console-border">
                {application.checklist.items.map((item, idx) => (
                  <div key={idx} className="py-3 flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2">
                      {item.status === 'VERIFIED' ? (
                        <CheckCircle className="h-4 w-4 text-emerald-400" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-amber-400" />
                      )}
                      <span className="font-medium text-console-text">{item.document_type}</span>
                      {item.required && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20">
                          Mandatory
                        </span>
                      )}
                    </div>
                    <StatusBadge status={item.status} />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-console-muted italic">No checklist requirement items configured.</p>
            )}
          </div>
        </div>

        {/* Right Column: Status Timeline & Submission Info */}
        <div className="space-y-6">
          <div className="glass-card p-5">
            <h3 className="text-xs font-semibold text-console-muted uppercase tracking-wider mb-4">
              Status Audit History
            </h3>
            <Timeline items={application.status_history || []} />
          </div>

          {application.submission && (
            <div className="glass-card p-5 space-y-2">
              <h3 className="text-xs font-semibold text-console-muted uppercase tracking-wider mb-2">
                External Submission Metadata
              </h3>
              <div className="text-xs font-mono space-y-1 text-console-muted">
                <p>Method: {application.submission.submission_method}</p>
                <p>External Ref: {application.submission.external_reference || 'N/A'}</p>
                <p>Provider Env: {application.submission.provider_environment || 'mock'}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
