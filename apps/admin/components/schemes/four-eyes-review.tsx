'use client';

import React, { useState } from 'react';
import { SchemeVersion } from '@/types/api';
import { publishSchemeVersion, submitSchemeVersionForReview } from '@/lib/api/schemes';
import { useAuth } from '@/lib/auth/auth-context';
import { StatusBadge } from '@/components/ui/status-badge';
import { ShieldCheck, Send, AlertTriangle, Lock } from 'lucide-react';

interface FourEyesReviewProps {
  version: SchemeVersion;
  onRefresh: () => void;
}

export function FourEyesReview({ version, onRefresh }: FourEyesReviewProps) {
  const { account } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmitForReview = async () => {
    setLoading(true);
    setError('');
    try {
      await submitSchemeVersionForReview(version.id);
      onRefresh();
    } catch (err: any) {
      setError(err.message || 'Failed to submit for review.');
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = async () => {
    setLoading(true);
    setError('');
    try {
      await publishSchemeVersion(version.id);
      onRefresh();
    } catch (err: any) {
      setError(err.message || 'Failed to publish scheme version.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card p-5 space-y-4">
      <div className="flex items-center justify-between border-b border-console-border pb-3">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="h-4 w-4 text-console-accent" />
          <h3 className="text-xs font-semibold text-console-muted uppercase tracking-wider">
            Four-Eyes Publishing Safety Control
          </h3>
        </div>
        <StatusBadge status={version.status} />
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
          {error}
        </div>
      )}

      {version.status === 'published' ? (
        <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center space-x-2">
          <Lock className="h-4 w-4 text-emerald-400 flex-shrink-0" />
          <span>
            This scheme version is <strong>PUBLISHED and IMMUTABLE</strong>. Published policy versions can never be edited directly. To alter policy, create a new draft version.
          </span>
        </div>
      ) : version.status === 'draft' ? (
        <div className="space-y-3">
          <p className="text-xs text-console-muted">
            Version #{version.version_no} is currently a <strong>DRAFT</strong>. Once eligibility rules pass validation and policy simulation, submit for secondary reviewer approval.
          </p>

          <div className="flex justify-end">
            <button
              onClick={handleSubmitForReview}
              disabled={loading}
              className="btn-primary text-xs bg-amber-600 hover:bg-amber-500 flex items-center space-x-1.5"
            >
              <Send className="h-4 w-4" />
              <span>Submit Version For Four-Eyes Review</span>
            </button>
          </div>
        </div>
      ) : version.status === 'in_review' ? (
        <div className="space-y-3">
          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-start space-x-2">
            <AlertTriangle className="h-4 w-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <span>
              Four-Eyes Rule Active: The second reviewer must be a different Scheme Admin from the original author. Self-publishing is rejected server-side.
            </span>
          </div>

          <div className="flex justify-end">
            <button
              onClick={handlePublish}
              disabled={loading}
              className="btn-primary text-xs bg-emerald-600 hover:bg-emerald-500 flex items-center space-x-1.5"
            >
              <ShieldCheck className="h-4 w-4" />
              <span>Approve & Publish Official Scheme Version</span>
            </button>
          </div>
        </div>
      ) : (
        <p className="text-xs text-console-muted italic">Terminal version state: {version.status}</p>
      )}
    </div>
  );
}
