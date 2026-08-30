import React from 'react';
import { CheckCircle2, Clock, AlertTriangle, XCircle, HelpCircle, FileText } from 'lucide-react';

interface StatusBadgeProps {
  status: string;
  type?: 'eligibility' | 'document' | 'application';
  className?: string;
}

interface StatusConfig {
  label: string;
  bgColor: string;
  textColor: string;
  icon: React.ComponentType<{ className?: string }>;
  accessibleDesc: string;
}

const statusMap: Record<string, StatusConfig> = {
  // Eligibility
  eligible: { label: '✓ Eligible', bgColor: 'bg-emerald-100', textColor: 'text-emerald-800', icon: CheckCircle2, accessibleDesc: 'You meet all scheme requirements' },
  likely_eligible: { label: '⚠ Likely Eligible', bgColor: 'bg-amber-100', textColor: 'text-amber-800', icon: AlertTriangle, accessibleDesc: 'You may be eligible subject to document verification' },
  not_eligible: { label: '✕ Not Eligible', bgColor: 'bg-rose-100', textColor: 'text-rose-800', icon: XCircle, accessibleDesc: 'You do not meet one or more scheme conditions' },
  insufficient_data: { label: '? Insufficient Data', bgColor: 'bg-slate-100', textColor: 'text-slate-700', icon: HelpCircle, accessibleDesc: 'Additional profile data required to evaluate eligibility' },

  // Document
  uploaded: { label: 'Uploaded', bgColor: 'bg-blue-100', textColor: 'text-blue-800', icon: FileText, accessibleDesc: 'Document uploaded' },
  processing: { label: 'Processing', bgColor: 'bg-purple-100', textColor: 'text-purple-800', icon: Clock, accessibleDesc: 'OCR and extraction in progress' },
  verified: { label: '✓ Verified', bgColor: 'bg-emerald-100', textColor: 'text-emerald-800', icon: CheckCircle2, accessibleDesc: 'Document verified successfully' },
  verification_required: { label: '⚠ Review Needed', bgColor: 'bg-amber-100', textColor: 'text-amber-800', icon: AlertTriangle, accessibleDesc: 'Citizen review and confirmation required' },
  rejected: { label: '✕ Rejected', bgColor: 'bg-rose-100', textColor: 'text-rose-800', icon: XCircle, accessibleDesc: 'Document rejected' },
  failed: { label: '✕ Failed', bgColor: 'bg-rose-100', textColor: 'text-rose-800', icon: XCircle, accessibleDesc: 'Document processing failed' },

  // Application
  draft: { label: 'Draft', bgColor: 'bg-slate-100', textColor: 'text-slate-700', icon: Clock, accessibleDesc: 'Application draft created' },
  submitted: { label: 'Submitted', bgColor: 'bg-blue-100', textColor: 'text-blue-800', icon: CheckCircle2, accessibleDesc: 'Application submitted successfully' },
  under_review: { label: 'Under Review', bgColor: 'bg-purple-100', textColor: 'text-purple-800', icon: Clock, accessibleDesc: 'Application currently being reviewed by case officer' },
  action_required: { label: '⚠ Action Required', bgColor: 'bg-amber-100', textColor: 'text-amber-800', icon: AlertTriangle, accessibleDesc: 'Citizen action or additional info required' },
  info_requested: { label: '⚠ Info Requested', bgColor: 'bg-amber-100', textColor: 'text-amber-800', icon: AlertTriangle, accessibleDesc: 'Additional documents or details requested' },
  approved: { label: '✓ Approved', bgColor: 'bg-emerald-100', textColor: 'text-emerald-800', icon: CheckCircle2, accessibleDesc: 'Application approved' },
  withdrawn: { label: 'Withdrawn', bgColor: 'bg-slate-100', textColor: 'text-slate-600', icon: XCircle, accessibleDesc: 'Application withdrawn by citizen' }
};

export function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const normalizedKey = status.toLowerCase();
  const config = statusMap[normalizedKey] || {
    label: status,
    bgColor: 'bg-slate-100',
    textColor: 'text-slate-700',
    icon: HelpCircle,
    accessibleDesc: status
  };

  const IconComponent = config.icon;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${config.bgColor} ${config.textColor} ${className}`}
      title={config.accessibleDesc}
      aria-label={config.accessibleDesc}
    >
      <IconComponent className="w-3.5 h-3.5" />
      <span>{config.label}</span>
    </span>
  );
}
