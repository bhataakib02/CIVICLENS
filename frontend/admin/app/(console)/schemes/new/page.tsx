'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createScheme } from '@/lib/api/schemes';
import { ArrowLeft, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function NewSchemePage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [category, setCategory] = useState('Agriculture');
  const [scope, setScope] = useState<'central' | 'state'>('central');
  const [dept, setDept] = useState('');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const scheme = await createScheme({
        canonical_name: name,
        category,
        scope,
        administering_dept: dept || undefined,
        code: code || undefined,
      });
      router.push(`/schemes/${scheme.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to create scheme.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center space-x-4">
        <Link href="/schemes" className="btn-secondary text-xs p-2">
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-console-text tracking-tight">Create Government Scheme</h1>
          <p className="text-xs text-console-muted">Define a new public scheme entity</p>
        </div>
      </div>

      <div className="glass-card p-6">
        {error && (
          <div className="mb-6 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-medium text-console-text mb-1">
              Canonical Scheme Name <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Pradhan Mantri Kisan Samman Nidhi"
              className="input-field w-full text-xs"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-medium text-console-text mb-1">Category</label>
              <input
                type="text"
                required
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="e.g. Agriculture, Housing"
                className="input-field w-full text-xs"
              />
            </div>

            <div>
              <label className="block font-medium text-console-text mb-1">Jurisdiction Scope</label>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as any)}
                className="input-field w-full text-xs"
              >
                <option value="central">Central Government</option>
                <option value="state">State Government</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-medium text-console-text mb-1">Administering Department</label>
              <input
                type="text"
                value={dept}
                onChange={(e) => setDept(e.target.value)}
                placeholder="e.g. Ministry of Agriculture"
                className="input-field w-full text-xs"
              />
            </div>

            <div>
              <label className="block font-medium text-console-text mb-1">Unique Scheme Code</label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                placeholder="e.g. PM_KISAN"
                className="input-field w-full text-xs font-mono"
              />
            </div>
          </div>

          <div className="flex justify-end pt-4">
            <button type="submit" disabled={loading} className="btn-primary text-xs flex items-center space-x-2">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <span>Create Scheme Entity</span>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
