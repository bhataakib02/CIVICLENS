'use client';

import React, { useState, useEffect } from 'react';
import {
  getAdminOpportunitySources,
  createAdminOpportunitySource,
  triggerManualCrawl,
  OpportunitySource,
} from '@/lib/api/opportunities';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/modal';
import { Globe, Plus, RefreshCw, Sparkles, ShieldCheck } from 'lucide-react';

export default function SourceRegistryPage() {
  const [sources, setSources] = useState<OpportunitySource[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [crawlingId, setCrawlingId] = useState<string | null>(null);

  const [name, setName] = useState('');
  const [domain, setDomain] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [sourceType, setSourceType] = useState('CENTRAL_GOVERNMENT');
  const [authorityLevel, setAuthorityLevel] = useState('OFFICIAL');
  const [crawlFrequency, setCrawlFrequency] = useState('30_minutes');

  const loadSources = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const list = await getAdminOpportunitySources();
      setSources(list);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch source registry.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSources();
  }, []);

  const handleCreateSource = async () => {
    try {
      await createAdminOpportunitySource({
        name,
        domain,
        base_url: baseUrl,
        source_type: sourceType,
        authority_level: authorityLevel,
        crawl_frequency: crawlFrequency,
        enabled: true,
      });
      setShowAddModal(false);
      setName('');
      setDomain('');
      setBaseUrl('');
      loadSources();
    } catch (err: any) {
      alert(err.message || 'Failed to register source.');
    }
  };

  const handleCrawlNow = async (id: string) => {
    setCrawlingId(id);
    try {
      await triggerManualCrawl(id);
      alert('Crawl job completed successfully.');
      loadSources();
    } catch (err: any) {
      alert('Crawl failed: ' + err.message);
    } finally {
      setCrawlingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white dark:bg-slate-900/90 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-indigo-500" />
            <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">Source Registry</h1>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Register and manage authoritative government and private opportunity sources.
          </p>
        </div>
        <Button onClick={() => setShowAddModal(true)} className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-bold px-4 py-2.5 rounded-xl shadow-md">
          <Plus className="w-4 h-4 mr-1.5" />
          Add New Source
        </Button>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {isLoading ? (
        <Skeleton className="h-64 rounded-3xl" />
      ) : (
        <div className="bg-white dark:bg-slate-900/90 rounded-3xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-xl">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/90 dark:bg-slate-950/90 text-slate-700 dark:text-slate-300 uppercase tracking-wider font-bold border-b border-slate-200 dark:border-slate-800 select-none">
              <tr>
                <th className="p-4">Source Name</th>
                <th className="p-4">Domain</th>
                <th className="p-4">Authority</th>
                <th className="p-4">Schedule</th>
                <th className="p-4">Last Crawled</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800/80 text-slate-800 dark:text-slate-200 font-medium">
              {sources.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400 dark:text-slate-500 italic">
                    No registered opportunity sources found.
                  </td>
                </tr>
              ) : (
                sources.map((src) => (
                  <tr key={src.id} className="hover:bg-indigo-500/5 dark:hover:bg-slate-800/60 transition-colors">
                    <td className="p-4 font-bold text-slate-900 dark:text-white">{src.name}</td>
                    <td className="p-4 font-mono text-xs text-slate-600 dark:text-slate-300">{src.domain}</td>
                    <td className="p-4">
                      <span className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20 text-[11px] font-bold px-2.5 py-0.5 rounded-full uppercase">
                        {src.authority_level}
                      </span>
                    </td>
                    <td className="p-4 text-xs font-semibold text-slate-600 dark:text-slate-400">{src.crawl_frequency}</td>
                    <td className="p-4 text-xs font-mono text-slate-500 dark:text-slate-400">
                      {src.last_crawled_at ? new Date(src.last_crawled_at).toLocaleString() : 'Never'}
                    </td>
                    <td className="p-4 text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={crawlingId === src.id}
                        onClick={() => handleCrawlNow(src.id)}
                        className="text-xs font-bold"
                      >
                        {crawlingId === src.id ? (
                          <span className="flex items-center gap-1">
                            <RefreshCw className="w-3 h-3 animate-spin" /> Crawling...
                          </span>
                        ) : (
                          'Crawl Now'
                        )}
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Register Source Modal */}
      <Modal isOpen={showAddModal} onClose={() => setShowAddModal(false)} title="Register Opportunity Source">
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Source Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. National Career Service"
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Domain</label>
            <input
              type="text"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              placeholder="e.g. ncs.gov.in"
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Base URL</label>
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="e.g. https://www.ncs.gov.in"
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Authority Level</label>
              <select
                value={authorityLevel}
                onChange={(e) => setAuthorityLevel(e.target.value)}
                className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white"
              >
                <option value="OFFICIAL">Official Government</option>
                <option value="VERIFIED_PARTNER">Verified Partner</option>
                <option value="KNOWN_PRIVATE">Known Private</option>
                <option value="UNVERIFIED">Unverified</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Crawl Frequency</label>
              <select
                value={crawlFrequency}
                onChange={(e) => setCrawlFrequency(e.target.value)}
                className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white"
              >
                <option value="30_minutes">30 Minutes</option>
                <option value="1_hour">1 Hour</option>
                <option value="3_hours">3 Hours</option>
                <option value="6_hours">6 Hours</option>
                <option value="daily">Daily</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-2">
            <Button variant="outline" onClick={() => setShowAddModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateSource} className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold">
              Save Source
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
