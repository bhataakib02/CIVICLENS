'use client';

import React, { useState } from 'react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { trackOpportunityApplication } from '@/lib/api/opportunities';

interface ApplicationTrackerModalProps {
  isOpen: boolean;
  onClose: () => void;
  opportunityId: string;
  opportunityTitle: string;
  onTracked?: () => void;
}

export function ApplicationTrackerModal({
  isOpen,
  onClose,
  opportunityId,
  opportunityTitle,
  onTracked,
}: ApplicationTrackerModalProps) {
  const [status, setStatus] = useState<'APPLIED' | 'INTERVIEW' | 'SELECTED' | 'REJECTED' | 'WITHDRAWN'>('APPLIED');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await trackOpportunityApplication(opportunityId, status, notes);
      if (onTracked) onTracked();
      onClose();
    } catch (err) {
      console.error('Failed to update tracker', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Track Application Status">
      <div className="space-y-4 text-slate-700">
        <p className="text-sm text-slate-600">
          Did you submit your application for <strong className="text-slate-900">{opportunityTitle}</strong> on the official portal? Keep track of your progress here.
        </p>

        <div>
          <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Status</label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as any)}
            className="w-full rounded-xl border border-slate-200 p-2.5 text-sm bg-white focus:ring-2 focus:ring-emerald-500"
          >
            <option value="APPLIED">Applied / Registered</option>
            <option value="INTERVIEW">Interview / Exam Scheduled</option>
            <option value="SELECTED">Selected / Offer Received</option>
            <option value="REJECTED">Not Selected / Rejected</option>
            <option value="WITHDRAWN">Withdrawn</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Notes / Registration ID (Optional)</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. Application No: APP-2026-98123"
            className="w-full rounded-xl border border-slate-200 p-2.5 text-sm bg-white focus:ring-2 focus:ring-emerald-500 h-20"
          />
        </div>

        <div className="flex justify-end space-x-3 pt-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting} className="bg-blue-600 hover:bg-blue-700 text-white font-medium">
            {isSubmitting ? 'Saving...' : 'Save Tracker Status'}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
