'use client';

import React, { useEffect, useState } from 'react';
import { getDocumentDownloadUrl } from '@/lib/api/documents';
import { ExternalLink, Lock, Eye, Loader2 } from 'lucide-react';

interface DocumentViewerProps {
  documentId: string;
  filename: string;
}

export function DocumentViewer({ documentId, filename }: DocumentViewerProps) {
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchUrl() {
      setLoading(true);
      setError('');
      try {
        const res = await getDocumentDownloadUrl(documentId);
        setDownloadUrl(res.download_url);
      } catch (err: any) {
        setError(err.message || 'Failed to generate secure viewing token.');
      } finally {
        setLoading(false);
      }
    }
    if (documentId) fetchUrl();
  }, [documentId]);

  return (
    <div className="glass-card p-5 space-y-4">
      <div className="flex items-center justify-between border-b border-console-border pb-3">
        <div className="flex items-center space-x-2">
          <Lock className="h-4 w-4 text-emerald-400" />
          <h3 className="text-xs font-semibold text-console-muted uppercase tracking-wider">
            Secure Signed Document Access
          </h3>
        </div>
        {downloadUrl && (
          <a
            href={downloadUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary text-xs flex items-center space-x-1.5"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            <span>Open Sealed Stream</span>
          </a>
        )}
      </div>

      <div className="p-3 rounded-lg bg-console-bg/80 border border-console-border text-xs text-console-muted leading-relaxed">
        <p className="flex items-center space-x-2 text-console-text font-medium mb-1">
          <Eye className="h-4 w-4 text-console-accent" />
          <span>Zero Internal Storage Leak Guarantee</span>
        </p>
        <p>
          Documents are retrieved exclusively via short-lived, time-bound HMAC signed tokens. Internal S3/GCS bucket names, storage keys, and credentials are never exposed in the UI.
        </p>
      </div>

      {loading ? (
        <div className="h-40 flex items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-console-accent" />
        </div>
      ) : error ? (
        <div className="p-3 rounded bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
          {error}
        </div>
      ) : downloadUrl ? (
        <div className="p-4 rounded-lg bg-console-bg border border-console-border text-center space-y-3">
          <p className="text-xs text-console-text font-mono truncate">{filename}</p>
          <a
            href={downloadUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary inline-flex items-center space-x-2 text-xs"
          >
            <span>View / Download Document Evidence</span>
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>
      ) : null}
    </div>
  );
}
