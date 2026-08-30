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
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      <div className="bg-white dark:bg-slate-900/90 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-indigo-500" />
            <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">Knowledge Base &amp; Provenance Console</h1>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Manage official government policy sources, ingestion pipeline, and trust verification.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl text-xs font-extrabold shadow-lg flex items-center justify-center gap-1.5 transition-all"
        >
          <Plus className="h-4 w-4" />
          <span>Ingest New Policy Source</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-semibold">
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
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-white dark:bg-slate-900 max-w-md w-full p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl space-y-4">
            <h3 className="text-lg font-extrabold text-slate-900 dark:text-white">Ingest Official Policy Source</h3>
            <form onSubmit={handleAddSource} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Source Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. West Bengal Lakshmir Bhandar Official Guidelines 2024"
                  className="w-full px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-medium"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Official Document / Portal URL</label>
                <input
                  type="url"
                  required
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://wb.gov.in/schemes/guidelines.pdf"
                  className="w-full px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-mono"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Publishing Department</label>
                <input
                  type="text"
                  value={publisher}
                  onChange={(e) => setPublisher(e.target.value)}
                  placeholder="e.g. Dept. of Women and Child Development"
                  className="w-full px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-medium"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-xl font-bold"
                >
                  Cancel
                </button>
                <button type="submit" disabled={submitLoading} className="px-4 py-2 bg-indigo-600 text-white rounded-xl font-bold flex items-center space-x-1.5 shadow-md">
                  {submitLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <span>Start Ingestion Job</span>}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
