'use client';

import React, { useState } from 'react';
import { ApplicationDetail } from '@/types/api';
import { reviewApplication, completeApplication } from '@/lib/api/applications';
import { InfoRequestDialog } from './info-request-dialog';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';
import { CheckCircle2, XCircle, HelpCircle, CheckCheck, Loader2 } from 'lucide-react';
import { useAuth } from '@/lib/auth/auth-context';
import { hasCapability } from '@/lib/permissions/roles';

interface ReviewActionsProps {
  application: ApplicationDetail;
  onRefresh: () => void;
}

export function ReviewActions({ application, onRefresh }: ReviewActionsProps) {
  const { account } = useAuth();
  const [loading, setLoading] = useState(false);
  const [showInfoDialog, setShowInfoDialog] = useState(false);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [error, setError] = useState('');

  const canReview = hasCapability(account?.role, 'canReviewApplications');
  if (!canReview) return null;

  const handleApprove = async () => {
    setLoading(true);
    setError('');
    try {
      await reviewApplication(application.id, { action: 'approve', reason: 'Verified by case worker.' });
      onRefresh();
    } catch (err: any) {
      setError(err.message || 'Failed to approve application.');
    } finally {
      setLoading(false);
      setShowApproveDialog(false);
    }
  };

  const handleReject = async (reason?: string) => {
    setLoading(true);
    setError('');
    try {
      await reviewApplication(application.id, { action: 'reject', reason });
      onRefresh();
    } catch (err: any) {
      setError(err.message || 'Failed to reject application.');
    } finally {
      setLoading(false);
      setShowRejectDialog(false);
    }
  };

  const handleInfoRequest = async (reason: string, requiredItems: string[]) => {
    setLoading(true);
    setError('');
    try {
      await reviewApplication(application.id, {
        action: 'request_action',
        reason,
        required_items: requiredItems,
      });
      onRefresh();
    } catch (err: any) {
      setError(err.message || 'Failed to request action.');
    } finally {
      setLoading(false);
      setShowInfoDialog(false);
    }
  };

  const handleComplete = async () => {
    setLoading(true);
    setError('');
    try {
      await completeApplication(application.id);
      onRefresh();
    } catch (err: any) {
      setError(err.message || 'Failed to complete application.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card p-5 space-y-4">
      <h3 className="text-xs font-semibold text-console-muted uppercase tracking-wider">Case Actions</h3>

      {error && <p className="text-xs text-red-400">{error}</p>}

      <div className="flex flex-wrap gap-3">
        {application.status === 'submitted' || application.status === 'under_review' ? (
          <>
            <button
              onClick={() => setShowApproveDialog(true)}
              disabled={loading}
              className="btn-primary text-xs bg-emerald-600 hover:bg-emerald-500 flex items-center space-x-2"
            >
              <CheckCircle2 className="h-4 w-4" />
              <span>Approve Application</span>
            </button>

            <button
              onClick={() => setShowInfoDialog(true)}
              disabled={loading}
              className="btn-secondary text-xs border-amber-500/30 text-amber-400 hover:bg-amber-500/10 flex items-center space-x-2"
            >
              <HelpCircle className="h-4 w-4" />
              <span>Request Information</span>
            </button>

            <button
              onClick={() => setShowRejectDialog(true)}
              disabled={loading}
              className="btn-danger text-xs flex items-center space-x-2"
            >
              <XCircle className="h-4 w-4" />
              <span>Reject Application</span>
            </button>
          </>
        ) : application.status === 'approved' ? (
          <button
            onClick={handleComplete}
            disabled={loading}
            className="btn-primary text-xs flex items-center space-x-2"
          >
            <CheckCheck className="h-4 w-4" />
            <span>Mark Benefit Delivered / Completed</span>
          </button>
        ) : (
          <p className="text-xs text-console-muted italic">No state transitions available for current status.</p>
        )}
      </div>

      <InfoRequestDialog
        isOpen={showInfoDialog}
        onClose={() => setShowInfoDialog(false)}
        onSubmit={handleInfoRequest}
      />

      <ConfirmDialog
        isOpen={showApproveDialog}
        title="Approve Application"
        message="Are you sure you want to approve this application? This decision will be permanently recorded in the audit log and dispatch a citizen notification."
        confirmLabel="Approve"
        confirmVariant="primary"
        onConfirm={handleApprove}
        onCancel={() => setShowApproveDialog(false)}
      />

      <ConfirmDialog
        isOpen={showRejectDialog}
        title="Reject Application"
        message="Are you sure you want to reject this application? You must provide an explicit operational reason."
        confirmLabel="Reject"
        confirmVariant="danger"
        requireReason={true}
        onConfirm={handleReject}
        onCancel={() => setShowRejectDialog(false)}
      />
    </div>
  );
}
