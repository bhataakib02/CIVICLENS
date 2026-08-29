'use client';

import React, { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  confirmVariant?: 'primary' | 'danger';
  requireReason?: boolean;
  onConfirm: (reason?: string) => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  confirmVariant = 'danger',
  requireReason = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleConfirm = () => {
    if (requireReason && !reason.trim()) {
      setError('A reason is required to perform this action.');
      return;
    }
    onConfirm(reason.trim() ? reason.trim() : undefined);
    setReason('');
    setError('');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="glass-elevated max-w-md w-full p-6 shadow-2xl animate-in fade-in zoom-in duration-200">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3 text-red-400">
            <AlertTriangle className="h-6 w-6 flex-shrink-0" />
            <h3 className="text-lg font-semibold text-console-text">{title}</h3>
          </div>
          <button onClick={onCancel} className="text-console-muted hover:text-console-text">
            <X className="h-5 w-5" />
          </button>
        </div>

        <p className="mt-3 text-sm text-console-muted leading-relaxed">{message}</p>

        {requireReason && (
          <div className="mt-4">
            <label className="block text-xs font-medium text-console-text mb-1">
              Reason for action <span className="text-red-400">*</span>
            </label>
            <textarea
              value={reason}
              onChange={(e) => {
                setReason(e.target.value);
                if (e.target.value.trim()) setError('');
              }}
              placeholder="Provide a specific operational reason..."
              rows={3}
              className="input-field w-full text-xs"
            />
            {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
          </div>
        )}

        <div className="mt-6 flex justify-end space-x-3">
          <button onClick={onCancel} className="btn-secondary text-xs">
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            className={confirmVariant === 'danger' ? 'btn-danger text-xs' : 'btn-primary text-xs'}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
