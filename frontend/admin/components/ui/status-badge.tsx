import React from 'react';
import { clsx } from 'clsx';
import { formatStatusLabel } from '@/lib/formatting';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const normalized = status.toLowerCase();

  const getStyle = (s: string) => {
    switch (s) {
      case 'published':
      case 'approved':
      case 'verified':
      case 'active':
      case 'completed':
      case 'eligible':
      case 'delivered':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';

      case 'under_review':
      case 'in_review':
      case 'processing':
      case 'validating':
      case 'submission_pending':
      case 'likely_eligible':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';

      case 'action_required':
      case 'info_requested':
      case 'verification_required':
      case 'draft':
      case 'pending':
      case 'insufficient_data':
      case 'stale':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';

      case 'rejected':
      case 'validation_failed':
      case 'processing_failed':
      case 'submission_failed':
      case 'failed':
      case 'not_eligible':
      case 'suspended':
        return 'bg-red-500/10 text-red-400 border-red-500/30';

      case 'withdrawn':
      case 'superseded':
      case 'archived':
      case 'cancelled':
        return 'bg-console-muted/10 text-console-muted border-console-muted/30';

      default:
        return 'bg-console-surface text-console-muted border-console-border';
    }
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border transition-colors',
        getStyle(normalized),
        className
      )}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5 opacity-75" />
      {formatStatusLabel(status)}
    </span>
  );
}
