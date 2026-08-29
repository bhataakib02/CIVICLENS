import React from 'react';
import Link from 'next/link';
import { FileQuestion, ArrowLeft } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-console-bg text-console-text">
      <div className="glass-elevated max-w-md w-full p-8 text-center">
        <div className="h-12 w-12 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 mx-auto flex items-center justify-center mb-4">
          <FileQuestion className="h-6 w-6" />
        </div>
        <h2 className="text-xl font-bold text-console-text">Resource Not Found</h2>
        <p className="mt-2 text-sm text-console-muted leading-relaxed">
          The console resource or record you requested does not exist or has been archived.
        </p>
        <div className="mt-6 flex justify-center">
          <Link href="/dashboard" className="btn-secondary text-xs flex items-center space-x-2">
            <ArrowLeft className="h-4 w-4" />
            <span>Return to Dashboard</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
