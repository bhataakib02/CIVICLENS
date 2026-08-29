'use client';

import React, { useState } from 'react';
import { X, AlertCircle } from 'lucide-react';

interface InfoRequestDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (reason: string, requiredItems: string[]) => void;
}

const DOCUMENT_OPTIONS = [
  'Income Certificate',
  'Residence Proof / Aadhaar',
  'Caste Certificate',
  'Disability Certificate',
  'Corrected Bank Passbook',
  'Land Record Proof',
];

export function InfoRequestDialog({ isOpen, onClose, onSubmit }: InfoRequestDialogProps) {
  const [reason, setReason] = useState('');
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const toggleDoc = (doc: string) => {
    if (selectedDocs.includes(doc)) {
      setSelectedDocs(selectedDocs.filter((d) => d !== doc));
    } else {
      setSelectedDocs([...selectedDocs, doc]);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) {
      setError('Please provide a specific reason for requesting additional information.');
      return;
    }
    onSubmit(reason.trim(), selectedDocs);
    setReason('');
    setSelectedDocs([]);
    setError('');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="glass-elevated max-w-lg w-full p-6 shadow-2xl">
        <div className="flex items-center justify-between border-b border-console-border pb-4">
          <h3 className="text-base font-semibold text-console-text">Request Missing Information / Documents</h3>
          <button onClick={onClose} className="text-console-muted hover:text-console-text">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-console-text mb-1">
              Required Document Checklist
            </label>
            <div className="space-y-2 max-h-40 overflow-y-auto p-3 rounded-lg bg-console-bg border border-console-border">
              {DOCUMENT_OPTIONS.map((doc) => (
                <label key={doc} className="flex items-center space-x-2 text-xs text-console-text cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedDocs.includes(doc)}
                    onChange={() => toggleDoc(doc)}
                    className="rounded border-console-border bg-console-surface text-console-accent focus:ring-console-accent"
                  />
                  <span>{doc}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-console-text mb-1">
              Instructions for Citizen <span className="text-red-400">*</span>
            </label>
            <textarea
              required
              rows={3}
              value={reason}
              onChange={(e) => {
                setReason(e.target.value);
                if (e.target.value.trim()) setError('');
              }}
              placeholder="Explain clearly what information or document is missing and why..."
              className="input-field w-full text-xs"
            />
          </div>

          <div className="flex justify-end space-x-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary text-xs">
              Cancel
            </button>
            <button type="submit" className="btn-primary text-xs">
              Dispatch Action Request
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
