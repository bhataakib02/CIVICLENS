'use client';

import React from 'react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Opportunity } from '@/lib/api/opportunities';

interface ApplyInterstitialModalProps {
  isOpen: boolean;
  onClose: () => void;
  opportunity: Opportunity | null;
  onConfirmedApply?: () => void;
}

export function ApplyInterstitialModal({
  isOpen,
  onClose,
  opportunity,
  onConfirmedApply,
}: ApplyInterstitialModalProps) {
  if (!opportunity) return null;

  const destinationUrl = opportunity.application_url || opportunity.source_url;
  const destinationDomain = opportunity.source_domain;

  const handleContinue = () => {
    if (onConfirmedApply) {
      onConfirmedApply();
    }
    window.open(destinationUrl, '_blank', 'noopener,noreferrer');
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Leaving CivicLens">
      <div className="space-y-4 text-slate-700">
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-sm">
          <p className="font-bold flex items-center gap-2">
            <span>🛡️</span> Official Website Redirect Confirmation
          </p>
          <p className="mt-1 text-amber-800">
            CivicLens routes you directly to the authoritative official website to apply. CivicLens does NOT collect your application credentials or submit applications on your behalf.
          </p>
        </div>

        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-sm space-y-2">
          <div>
            <span className="text-slate-400 font-medium block text-xs uppercase">Opportunity</span>
            <span className="font-semibold text-slate-900">{opportunity.title}</span>
          </div>
          <div>
            <span className="text-slate-400 font-medium block text-xs uppercase">Organization</span>
            <span className="font-medium text-slate-800">{opportunity.organization}</span>
          </div>
          <div>
            <span className="text-slate-400 font-medium block text-xs uppercase">Verified Official Source</span>
            <span className="font-mono text-emerald-700 font-semibold">{opportunity.source_name} ({destinationDomain})</span>
          </div>
          <div>
            <span className="text-slate-400 font-medium block text-xs uppercase">Last Verification</span>
            <span className="text-slate-600">Verified {new Date(opportunity.last_verified_at).toLocaleDateString()}</span>
          </div>
        </div>

        <div className="flex justify-end space-x-3 pt-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleContinue} className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium">
            Continue to Official Website &rarr;
          </Button>
        </div>
      </div>
    </Modal>
  );
}
