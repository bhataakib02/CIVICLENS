'use client';

import React from 'react';
import { useAuth } from '@/lib/auth/auth-context';
import { Shield, Bell } from 'lucide-react';
import { StatusBadge } from '@/components/ui/status-badge';
import { ThemeToggle } from './theme-toggle';

export function Header() {
  const { account } = useAuth();

  return (
    <header className="h-14 bg-white/80 dark:bg-console-surface/80 backdrop-blur-md border-b border-slate-200 dark:border-console-border px-6 flex items-center justify-between sticky top-0 z-30 transition-colors duration-200">
      <div className="flex items-center space-x-3">
        <span className="text-xs text-slate-500 dark:text-console-muted">Environment:</span>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30">
          OPERATIONAL PROD
        </span>
      </div>

      <div className="flex items-center space-x-4">
        <ThemeToggle />
        {account && (
          <div className="flex items-center space-x-2 border-r border-slate-200 dark:border-console-border pr-4">
            <Shield className="h-4 w-4 text-indigo-600 dark:text-console-accent" />
            <span className="text-xs text-slate-800 dark:text-console-text font-mono capitalize">{account.role}</span>
            <StatusBadge status={account.status} />
          </div>
        )}

        <div className="text-xs text-slate-500 dark:text-console-muted font-mono">
          {new Date().toLocaleDateString('en-IN', {
            weekday: 'short',
            day: '2-digit',
            month: 'short',
            year: 'numeric',
          })}
        </div>
      </div>
    </header>
  );
}
