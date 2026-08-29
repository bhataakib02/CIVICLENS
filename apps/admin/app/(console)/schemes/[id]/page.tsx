'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  getScheme,
  getSchemeVersions,
  getVersionRules,
  createSchemeVersion,
  setVersionRules,
} from '@/lib/api/schemes';
import { EligibilityRule, SchemeDetail, SchemeVersion } from '@/types/api';
import { RuleEditor } from '@/components/schemes/rule-editor';
import { FourEyesReview } from '@/components/schemes/four-eyes-review';
import { StatusBadge } from '@/components/ui/status-badge';
import { formatDate } from '@/lib/formatting';
import { ArrowLeft, Plus, Play, Layers, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function SchemeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [scheme, setScheme] = useState<SchemeDetail | null>(null);
  const [versions, setVersions] = useState<SchemeVersion[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<SchemeVersion | null>(null);
  const [rules, setRules] = useState<EligibilityRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [rulesLoading, setRulesLoading] = useState(false);
  const [error, setError] = useState('');
  const [showNewVersionModal, setShowNewVersionModal] = useState(false);

  // New version state
  const [benefitsSummary, setBenefitsSummary] = useState('');
  const [effectiveFrom, setEffectiveFrom] = useState(new Date().toISOString().split('T')[0]);

  const fetchSchemeAndVersions = async () => {
    setLoading(true);
    setError('');
    try {
      const s = await getScheme(id);
      const vs = await getSchemeVersions(id);
      setScheme(s);
      setVersions(vs);

      if (vs.length > 0) {
        const latest = vs[0];
        setSelectedVersion(latest);
        await fetchRules(latest.id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load scheme details.');
    } finally {
      setLoading(false);
    }
  };

  const fetchRules = async (versionId: string) => {
    setRulesLoading(true);
    try {
      const r = await getVersionRules(versionId);
      setRules(r);
    } catch (err) {
      setRules([]);
    } finally {
      setRulesLoading(false);
    }
  };

  useEffect(() => {
    if (id) fetchSchemeAndVersions();
  }, [id]);

  const handleSelectVersion = async (v: SchemeVersion) => {
    setSelectedVersion(v);
    await fetchRules(v.id);
  };

  const handleCreateVersion = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const newV = await createSchemeVersion(id, {
        benefits_summary: benefitsSummary,
        effective_from: effectiveFrom,
      });
      setShowNewVersionModal(false);
      await fetchSchemeAndVersions();
      handleSelectVersion(newV);
    } catch (err: any) {
      alert(err.message || 'Failed to create new draft version.');
    }
  };

  const handleSaveRules = async (updatedRules: any[]) => {
    if (!selectedVersion) return;
    try {
      await setVersionRules(selectedVersion.id, updatedRules);
      await fetchRules(selectedVersion.id);
      alert('Eligibility rules saved and validated.');
    } catch (err: any) {
      alert(err.message || 'Failed to save eligibility rules.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link href="/schemes" className="btn-secondary text-xs p-2">
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-console-text tracking-tight">
              {scheme?.canonical_name || 'Scheme Detail'}
            </h1>
            <p className="text-xs text-console-muted font-mono">
              ID: {id} | Scope: {scheme?.scope?.toUpperCase()} | Category: {scheme?.category}
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowNewVersionModal(true)}
          className="btn-secondary text-xs flex items-center space-x-1.5"
        >
          <Plus className="h-4 w-4" />
          <span>Create New Draft Version</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
          {error}
        </div>
      )}

      {loading && !scheme ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-console-accent" />
        </div>
      ) : scheme ? (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Version Selector Sidebar */}
          <div className="glass-card p-4 space-y-3">
            <h3 className="text-xs font-semibold text-console-muted uppercase tracking-wider">
              Version History
            </h3>
            <div className="space-y-2">
              {versions.map((v: SchemeVersion) => {
                const isSelected = selectedVersion?.id === v.id;
                return (
                  <div
                    key={v.id}
                    onClick={() => handleSelectVersion(v)}
                    className={`p-3 rounded-lg border text-xs cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-console-accent/10 border-console-accent text-console-text font-semibold'
                        : 'bg-console-bg/50 border-console-border text-console-muted hover:bg-console-elevated'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span>Version #{v.version_no}</span>
                      <StatusBadge status={v.status} />
                    </div>
                    <p className="text-[11px] font-mono text-console-muted">
                      From: {formatDate(v.effective_from)}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Version Detail & Rule Editor */}
          <div className="lg:col-span-3 space-y-6">
            {selectedVersion && (
              <>
                {/* Four-Eyes Control */}
                <FourEyesReview version={selectedVersion} onRefresh={fetchSchemeAndVersions} />

                {/* Simulation Link */}
                <div className="flex justify-end">
                  <button
                    onClick={() => router.push(`/schemes/${id}/simulate?versionId=${selectedVersion.id}`)}
                    className="btn-primary text-xs bg-indigo-600 hover:bg-indigo-500 flex items-center space-x-1.5"
                  >
                    <Play className="h-4 w-4" />
                    <span>Open Policy Simulation Engine</span>
                  </button>
                </div>

                {/* Rule Editor */}
                {rulesLoading ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-console-accent" />
                  </div>
                ) : (
                  <RuleEditor
                    initialRules={rules}
                    onSave={handleSaveRules}
                    disabled={selectedVersion.status === 'published' || selectedVersion.status === 'superseded'}
                  />
                )}
              </>
            )}
          </div>
        </div>
      ) : null}

      {/* New Version Modal */}
      {showNewVersionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="glass-elevated max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-base font-semibold text-console-text mb-4">Create New Draft Version</h3>
            <form onSubmit={handleCreateVersion} className="space-y-4 text-xs">
              <div>
                <label className="block font-medium text-console-text mb-1">Benefits Summary</label>
                <textarea
                  required
                  rows={3}
                  value={benefitsSummary}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setBenefitsSummary(e.target.value)}
                  placeholder="Summarize benefits provided under this version..."
                  className="input-field w-full text-xs"
                />
              </div>

              <div>
                <label className="block font-medium text-console-text mb-1">Effective From Date</label>
                <input
                  type="date"
                  required
                  value={effectiveFrom}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEffectiveFrom(e.target.value)}
                  className="input-field w-full text-xs font-mono"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewVersionModal(false)}
                  className="btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary text-xs">
                  Create Draft Version
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
