'use client';

import React, { useState } from 'react';
import { DocumentDetail } from '@/types/api';
import { confirmDocumentExtraction } from '@/lib/api/documents';
import { useTranslation } from '@/lib/i18n';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert } from '@/components/ui/alert';
import { FileCheck, ShieldCheck, CheckCircle2 } from 'lucide-react';

interface ExtractionReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  documentDetail: DocumentDetail;
  onConfirmed: () => void;
}

export function ExtractionReviewModal({
  isOpen,
  onClose,
  documentDetail,
  onConfirmed
}: ExtractionReviewModalProps) {
  const { t } = useTranslation();
  const initialFields = documentDetail.extracted_fields || {};
  const [fields, setFields] = useState<Record<string, string>>(() => {
    const formatted: Record<string, string> = {};
    Object.keys(initialFields).forEach((k) => {
      const val = initialFields[k];
      formatted[k] = typeof val === 'object' ? val.value || JSON.stringify(val) : String(val ?? '');
    });
    return formatted;
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFieldChange = (key: string, val: string) => {
    setFields((prev) => ({ ...prev, [key]: val }));
  };

  const handleConfirm = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      await confirmDocumentExtraction(documentDetail.id, fields);
      onConfirmed();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to confirm extracted details.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const confidencePct = Math.round((documentDetail.confidence || 0.95) * 100);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={t.documents.reviewExtraction}>
      <div className="space-y-6">
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex items-center justify-between">
          <div>
            <h4 className="font-bold text-slate-900 text-sm capitalize">{documentDetail.document_type}</h4>
            <p className="text-xs text-slate-500">ID: {documentDetail.id.slice(0, 8)}</p>
          </div>
          <div className="text-right">
            <span className="text-xs text-slate-500 block">{t.documents.confidence}</span>
            <span className="text-sm font-extrabold text-emerald-700">{confidencePct}%</span>
          </div>
        </div>

        <Alert type="info">
          <p className="text-xs">
            Extracted from your uploaded document. Please verify the values below before confirming for scheme processing.
          </p>
        </Alert>

        {error && <Alert type="error">{error}</Alert>}

        <div className="space-y-3">
          {Object.keys(fields).length === 0 ? (
            <p className="text-xs text-slate-500 italic">No structured fields extracted.</p>
          ) : (
            Object.keys(fields).map((key) => (
              <div key={key} className="p-3 bg-white border border-slate-200 rounded-xl space-y-1">
                <label className="block text-xs font-semibold text-slate-700 capitalize">
                  {key.replace(/_/g, ' ')}
                </label>
                <Input
                  value={fields[key]}
                  onChange={(e) => handleFieldChange(key, e.target.value)}
                  className="bg-slate-50 text-sm"
                />
              </div>
            ))
          )}
        </div>

        <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
          <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
            {t.common.cancel}
          </Button>
          <Button onClick={handleConfirm} isLoading={isSubmitting}>
            <CheckCircle2 className="w-4 h-4 mr-1.5" />
            {t.documents.confirmExtraction}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
