'use client';

import React, { useState } from 'react';
import { DocumentDetail, ExtractedField } from '@/types/api';
import { confirmDocumentVerification } from '@/lib/api/documents';
import { StatusBadge } from '@/components/ui/status-badge';
import { CheckCircle2, XCircle, Edit3, Save, AlertTriangle } from 'lucide-react';

interface VerificationPanelProps {
  document: DocumentDetail;
  onRefresh: () => void;
}

export function VerificationPanel({ document, onRefresh }: VerificationPanelProps) {
  const [editing, setEditing] = useState(false);
  const [correctedFields, setCorrectedFields] = useState<Record<string, string>>({});
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fields: ExtractedField[] = document.fields || [];

  const handleFieldChange = (fieldName: string, val: string) => {
    setCorrectedFields((prev) => ({ ...prev, [fieldName]: val }));
  };

  const handleConfirm = async (action: 'confirm' | 'correct' | 'reject') => {
    setLoading(true);
    setError('');
    try {
      await confirmDocumentVerification(document.id, {
        action,
        corrected_fields: action === 'correct' ? correctedFields : undefined,
        correction_reason: action === 'correct' ? reason : undefined,
      });
      setEditing(false);
      onRefresh();
    } catch (err: any) {
      setError(err.message || 'Failed to update verification status.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card p-5 space-y-5">
      <div className="flex items-center justify-between border-b border-console-border pb-3">
        <div>
          <h3 className="text-xs font-semibold text-console-muted uppercase tracking-wider">
            OCR & Field Extraction Evidence
          </h3>
          <p className="text-[11px] text-console-muted mt-0.5 font-mono">
            Confidence: {document.confidence ? `${Math.round(document.confidence * 100)}%` : 'N/A'} | OCR Status:{' '}
            {document.processing_status || 'completed'}
          </p>
        </div>
        <StatusBadge status={document.status} />
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {/* Extracted Fields Table */}
      {fields.length > 0 ? (
        <div className="space-y-3">
          <div className="overflow-x-auto rounded-lg border border-console-border">
            <table className="w-full text-left text-xs">
              <thead className="bg-console-surface text-console-muted uppercase tracking-wider">
                <tr>
                  <th className="px-3 py-2">Field Name</th>
                  <th className="px-3 py-2">Extracted Value</th>
                  <th className="px-3 py-2">Verified Value</th>
                  <th className="px-3 py-2">Confidence</th>
                  <th className="px-3 py-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-console-border">
                {fields.map((f) => (
                  <tr key={f.field_name}>
                    <td className="px-3 py-2 font-mono font-medium text-console-text">{f.field_name}</td>
                    <td className="px-3 py-2 font-mono text-console-muted">{f.raw_value || f.normalized_value || '—'}</td>
                    <td className="px-3 py-2 font-mono text-console-text">
                      {editing ? (
                        <input
                          type="text"
                          defaultValue={f.verified_value || f.normalized_value || f.raw_value || ''}
                          onChange={(e) => handleFieldChange(f.field_name, e.target.value)}
                          className="input-field text-xs py-1 px-2 w-full"
                        />
                      ) : (
                        f.verified_value || f.normalized_value || f.raw_value || '—'
                      )}
                    </td>
                    <td className="px-3 py-2 font-mono">
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded ${
                          f.confidence_level === 'high'
                            ? 'bg-emerald-500/10 text-emerald-400'
                            : 'bg-amber-500/10 text-amber-400'
                        }`}
                      >
                        {Math.round((f.confidence || 0) * 100)}% ({f.confidence_level})
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <StatusBadge status={f.verification_status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {editing && (
            <div className="pt-2">
              <label className="block text-xs font-medium text-console-text mb-1">
                Correction Justification / Audit Note <span className="text-red-400">*</span>
              </label>
              <textarea
                required
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Specify why fields were corrected..."
                rows={2}
                className="input-field w-full text-xs"
              />
            </div>
          )}
        </div>
      ) : (
        <p className="text-xs text-console-muted italic">No structured fields extracted from document.</p>
      )}

      {/* Decision Buttons */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-console-border">
        {!editing ? (
          <>
            <button
              onClick={() => handleConfirm('confirm')}
              disabled={loading}
              className="btn-primary text-xs bg-emerald-600 hover:bg-emerald-500 flex items-center space-x-1.5"
            >
              <CheckCircle2 className="h-4 w-4" />
              <span>Verify & Confirm Extracted Fields</span>
            </button>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setEditing(true)}
                disabled={loading}
                className="btn-secondary text-xs flex items-center space-x-1.5"
              >
                <Edit3 className="h-4 w-4" />
                <span>Correct Fields</span>
              </button>

              <button
                onClick={() => handleConfirm('reject')}
                disabled={loading}
                className="btn-danger text-xs flex items-center space-x-1.5"
              >
                <XCircle className="h-4 w-4" />
                <span>Reject Document</span>
              </button>
            </div>
          </>
        ) : (
          <div className="flex items-center space-x-3 w-full justify-end">
            <button onClick={() => setEditing(false)} className="btn-secondary text-xs">
              Cancel
            </button>
            <button
              onClick={() => handleConfirm('correct')}
              disabled={loading || !reason.trim()}
              className="btn-primary text-xs flex items-center space-x-1.5"
            >
              <Save className="h-4 w-4" />
              <span>Save Corrections & Verify</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
