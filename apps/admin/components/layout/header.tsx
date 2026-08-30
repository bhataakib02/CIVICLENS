'use client';

import React from 'react';
import { useAuth } from '@/lib/auth/auth-context';
import { ShieldCheck, Activity, Clock } from 'lucide-react';
import { StatusBadge } from '@/components/ui/status-badge';
import { ThemeToggle } from './theme-toggle';

export function Header() {
  const { account } = useAuth();

  return (
    <header className="h-16 bg-white/90 dark:bg-slate-950/90 backdrop-blur-2xl border-b border-slate-200 dark:border-slate-800/80 px-6 flex items-center justify-between sticky top-0 z-30 transition-colors duration-300 shadow-sm">
      {/* Left Environment Badge */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-bold">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>OPERATIONAL PRODUCTION</span>
        </div>
        <span className="text-xs text-slate-400 dark:text-slate-500 hidden sm:inline">|</span>
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 hidden sm:inline flex items-center gap-1">
          <Activity className="w-3.5 h-3.5 text-blue-500" /> All Services Operational
        </span>
      </div>

      {/* Right Controls & Role */}
      <div className="flex items-center space-x-4">
        <ThemeToggle />

        {account && (
          <div className="flex items-center space-x-2 border-l border-slate-200 dark:border-slate-800 pl-4">
            <ShieldCheck className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            <span className="text-xs text-slate-800 dark:text-slate-200 font-bold uppercase tracking-wider font-mono">
              {account.role}
            </span>
            <StatusBadge status={account.status} />
          </div>
        )}

        <div className="text-xs text-slate-500 dark:text-slate-400 font-semibold font-mono flex items-center gap-1 bg-slate-100 dark:bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>
            {new Date().toLocaleDateString('en-IN', {
              weekday: 'short',
              day: '2-digit',
              month: 'short',
              year: 'numeric',
            })}
          </span>
        </div>
      </div>
    </header>
  );
}
