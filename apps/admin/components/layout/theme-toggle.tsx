'use client';

import React from 'react';
import { useTheme } from '@/lib/theme/theme-context';
import { Sun, Moon } from 'lucide-react';

export function ThemeToggle({ className = '' }: { className?: string }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`p-1.5 rounded-lg border transition-all duration-200 flex items-center justify-center ${
        theme === 'dark'
          ? 'bg-console-surface text-amber-300 border-console-border hover:bg-console-elevated'
          : 'bg-slate-100 text-slate-700 border-slate-300 hover:bg-slate-200'
      } ${className}`}
      title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
      aria-label="Toggle admin theme"
    >
      {theme === 'dark' ? (
        <Sun className="w-3.5 h-3.5 transition-transform hover:rotate-45" />
      ) : (
        <Moon className="w-3.5 h-3.5 transition-transform hover:-rotate-12" />
      )}
    </button>
  );
}
