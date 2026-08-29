'use client';

import React from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-console-bg text-console-text">
      <div className="glass-elevated max-w-md w-full p-8 text-center">
        <div className="h-12 w-12 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 mx-auto flex items-center justify-center mb-4">
          <AlertOctagon className="h-6 w-6" />
        </div>
        <h2 className="text-xl font-bold text-console-text">Operational Error</h2>
        <p className="mt-2 text-sm text-console-muted leading-relaxed">
          {error.message || 'An unexpected error occurred in the console.'}
        </p>
        <div className="mt-6 flex justify-center">
          <button onClick={reset} className="btn-primary text-xs flex items-center space-x-2">
            <RefreshCw className="h-4 w-4" />
            <span>Retry Operation</span>
          </button>
        </div>
      </div>
    </div>
  );
}
