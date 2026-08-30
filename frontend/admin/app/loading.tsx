import React from 'react';
import { Loader2 } from 'lucide-react';

export default function Loading() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-console-bg text-console-muted space-y-3">
      <Loader2 className="h-8 w-8 animate-spin text-console-accent" />
      <p className="text-xs font-mono tracking-wider uppercase">Loading Console Data...</p>
    </div>
  );
}
