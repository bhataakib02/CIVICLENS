import React from 'react';
import { ShieldCheck } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-400 text-xs py-8 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-white font-semibold text-sm">
          <ShieldCheck className="w-5 h-5 text-blue-400" />
          <span>CivicLens Platform</span>
        </div>
        <p className="text-center sm:text-left">
          Official deterministic public service engine. AI responses cite government knowledge sources.
        </p>
        <div className="flex items-center gap-4 text-slate-400">
          <span>v1.0 Production</span>
          <span>•</span>
          <span>Accessibility Compliant</span>
        </div>
      </div>
    </footer>
  );
}
