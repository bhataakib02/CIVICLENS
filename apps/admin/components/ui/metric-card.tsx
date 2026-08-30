import React from 'react';
import { LucideIcon, TrendingUp } from 'lucide-react';
import { clsx } from 'clsx';

interface MetricCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon?: LucideIcon;
  variant?: 'neutral' | 'info' | 'warning' | 'danger' | 'success';
  trend?: string;
  onClick?: () => void;
  className?: string;
}

export function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'neutral',
  trend,
  onClick,
  className = '',
}: MetricCardProps) {
  const getVariantStyles = () => {
    switch (variant) {
      case 'info':
        return {
          card: 'border-indigo-500/30 dark:border-indigo-500/20 bg-indigo-500/5 hover:border-indigo-500/50 shadow-lg shadow-indigo-950/20',
          iconBg: 'bg-gradient-to-tr from-indigo-600 to-blue-500 text-white shadow-md shadow-indigo-500/30',
          badge: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
        };
      case 'warning':
        return {
          card: 'border-amber-500/30 dark:border-amber-500/20 bg-amber-500/5 hover:border-amber-500/50 shadow-lg shadow-amber-950/20',
          iconBg: 'bg-gradient-to-tr from-amber-600 to-orange-500 text-white shadow-md shadow-amber-500/30',
          badge: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
        };
      case 'danger':
        return {
          card: 'border-red-500/30 dark:border-red-500/20 bg-red-500/5 hover:border-red-500/50 shadow-lg shadow-red-950/20',
          iconBg: 'bg-gradient-to-tr from-red-600 to-rose-500 text-white shadow-md shadow-red-500/30',
          badge: 'bg-red-500/10 text-red-400 border-red-500/20',
        };
      case 'success':
        return {
          card: 'border-emerald-500/30 dark:border-emerald-500/20 bg-emerald-500/5 hover:border-emerald-500/50 shadow-lg shadow-emerald-950/20',
          iconBg: 'bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-md shadow-emerald-500/30',
          badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
        };
      default:
        return {
          card: 'border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-900/80 hover:border-slate-300 dark:hover:border-slate-700 shadow-lg shadow-slate-950/10',
          iconBg: 'bg-gradient-to-tr from-slate-700 to-slate-900 text-white shadow-md shadow-slate-800/30',
          badge: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
        };
    }
  };

  const style = getVariantStyles();

  return (
    <div
      onClick={onClick}
      className={clsx(
        'glass-card p-6 transition-all duration-300 rounded-2xl relative overflow-hidden group',
        style.card,
        onClick && 'cursor-pointer hover:-translate-y-1 active:translate-y-0',
        className
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            {title}
          </p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 dark:text-white font-mono tracking-tight">
              {value}
            </span>
            {trend && (
              <span className={clsx('inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full border', style.badge)}>
                <TrendingUp className="w-3 h-3 mr-0.5" />
                {trend}
              </span>
            )}
          </div>
        </div>

        {Icon && (
          <div className={clsx('p-3 rounded-xl flex items-center justify-center flex-shrink-0 transition-transform group-hover:scale-110 duration-300', style.iconBg)}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>

      {subtitle && (
        <p className="mt-3 text-xs font-medium text-slate-500 dark:text-slate-400 border-t border-slate-100 dark:border-slate-800/60 pt-2.5">
          {subtitle}
        </p>
      )}
    </div>
  );
}
