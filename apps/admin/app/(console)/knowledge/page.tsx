'use client';

import React, { useEffect, useState } from 'react';
import { SourceTable } from '@/components/knowledge/source-table';
import { TableSkeleton } from '@/components/ui/loading-skeleton';
import { createKnowledgeSource, getKnowledgeSources, verifyKnowledgeSource } from '@/lib/api/knowledge';
import { KnowledgeSource } from '@/types/api';
import { Plus, BookOpen, ExternalLink, ShieldCheck, Loader2 } from 'lucide-react';

export default function KnowledgePage() {
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  // Form state
  const [title, setTitle] = useState('');
  const [url, setUrl] = useState('');
  const [publisher, setPublisher] = useState('');
  const [submitLoading, setSubmitLoading] = useState(false);

  const fetchSources = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getKnowledgeSources();
      setSources(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load knowledge sources.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
  }, []);

  const handleAddSource = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitLoading(true);
    try {
      await createKnowledgeSource({ title, url, publisher: publisher || undefined });
      setShowAddModal(false);
      setTitle('');
      setUrl('');
      setPublisher('');
      await fetchSources();
    } catch (err: any) {
      alert(err.message || 'Failed to submit knowledge source for ingestion.');
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleVerifySource = async (sourceId: string, status: 'verified' | 'rejected') => {
    try {
      await verifyKnowledgeSource(sourceId, {
        verification_status: status,
        trust_level: 'official_government',
      });
      await fetchSources();
    } catch (err: any) {
      alert(err.message || 'Failed to update source verification.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-console-text tracking-tight">Knowledge Base & Provenance Console</h1>
          <p className="text-xs text-console-muted mt-1">Manage official government policy sources, ingestion pipeline, and trust verification</p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="btn-primary text-xs flex items-center space-x-1.5"
        >
          <Plus className="h-4 w-4" />
          <span>Ingest New Policy Source</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
          {error}
        </div>
      )}

      {loading ? (
        <TableSkeleton rows={8} cols={5} />
      ) : (
        <SourceTable
          sources={sources}
          onSelect={(s) => {
            if (s.verification_status === 'pending') {
              if (confirm(`Verify source provenance for "${s.title}" as Official Government Content?`)) {
                handleVerifySource(s.id, 'verified');
              }
            }
          }}
        />
      )}

      {/* Ingest Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="glass-elevated max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-base font-semibold text-console-text mb-4">Ingest Official Policy Source</h3>
            <form onSubmit={handleAddSource} className="space-y-4 text-xs">
              <div>
                <label className="block font-medium text-console-text mb-1">Source Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. West Bengal Lakshmir Bhandar Official Guidelines 2024"
                  className="input-field w-full text-xs"
                />
              </div>

              <div>
                <label className="block font-medium text-console-text mb-1">Official Document / Portal URL</label>
                <input
                  type="url"
                  required
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://wb.gov.in/schemes/guidelines.pdf"
                  className="input-field w-full text-xs font-mono"
                />
              </div>

              <div>
                <label className="block font-medium text-console-text mb-1">Publishing Department</label>
                <input
                  type="text"
                  value={publisher}
                  onChange={(e) => setPublisher(e.target.value)}
                  placeholder="e.g. Dept. of Women and Child Development"
                  className="input-field w-full text-xs"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button type="submit" disabled={submitLoading} className="btn-primary text-xs flex items-center space-x-1.5">
                  {submitLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <span>Start Async Ingestion Job</span>}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
