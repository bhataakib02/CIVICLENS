'use client';

import React, { useState } from 'react';
import { ApplicationDetail } from '@/types/api';
import { submitApplication } from '@/lib/api/applications';
import { useTranslation } from '@/lib/i18n';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Alert } from '@/components/ui/alert';
import { ShieldCheck, FileCheck, CheckCircle } from 'lucide-react';

interface SubmitConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  applicationDetail: ApplicationDetail;
  onSubmitted: () => void;
}

export function SubmitConfirmationModal({
  isOpen,
  onClose,
  applicationDetail,
  onSubmitted
}: SubmitConfirmationModalProps) {
  const { t } = useTranslation();
  const [consentChecked, setConsentChecked] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!consentChecked) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await submitApplication(applicationDetail.id);
      onSubmitted();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to submit application package.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={t.applications.confirmSubmission}>
      <div className="space-y-6">
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs space-y-2">
          <div className="flex justify-between">
            <span className="text-slate-500">{t.applications.appId}</span>
            <span className="font-mono font-bold text-slate-900">{applicationDetail.id}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Scheme ID</span>
            <span className="font-bold text-slate-900">{applicationDetail.scheme_id}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Attached Documents</span>
            <span className="font-bold text-slate-900">{applicationDetail.attached_documents?.length || 0} files</span>
          </div>
        </div>

        <Alert type="info">
          <p className="text-xs">
            Once submitted, your application package will be sent to the official administering department for review.
          </p>
        </Alert>

        {error && <Alert type="error">{error}</Alert>}

        {/* Declaration Box with Explicit Consent */}
        <div className="p-4 bg-amber-50/60 border border-amber-200 rounded-xl space-y-3">
          <div className="flex items-start gap-2">
            <ShieldCheck className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-amber-900 leading-relaxed font-medium">
              {t.applications.declaration}
            </p>
          </div>

          <label className="flex items-center gap-3 cursor-pointer pt-2 border-t border-amber-200/60">
            <input
              type="checkbox"
              checked={consentChecked}
              onChange={(e) => setConsentChecked(e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500"
            />
            <span className="text-xs font-bold text-slate-900">
              I agree to the declaration and authorize application processing.
            </span>
          </label>
        </div>

        <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
          <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
            {t.common.cancel}
          </Button>
          <Button
            onClick={handleSubmit}
            isLoading={isSubmitting}
            disabled={!consentChecked}
          >
            <CheckCircle className="w-4 h-4 mr-1.5" />
            {t.applications.submitAppBtn}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
