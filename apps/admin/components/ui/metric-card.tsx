import React from 'react';
import { LucideIcon } from 'lucide-react';
import { clsx } from 'clsx';

interface MetricCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon?: LucideIcon;
  variant?: 'neutral' | 'info' | 'warning' | 'danger' | 'success';
  onClick?: () => void;
  className?: string;
}

export function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'neutral',
  onClick,
  className = '',
}: MetricCardProps) {
  const getVariantStyles = () => {
    switch (variant) {
      case 'info':
        return 'border-blue-500/30 bg-blue-500/5 text-blue-400';
      case 'warning':
        return 'border-amber-500/30 bg-amber-500/5 text-amber-400';
      case 'danger':
        return 'border-red-500/30 bg-red-500/5 text-red-400';
      case 'success':
        return 'border-emerald-500/30 bg-emerald-500/5 text-emerald-400';
      default:
        return 'border-console-border bg-console-surface/80 text-console-muted';
    }
  };

  return (
    <div
      onClick={onClick}
      className={clsx(
        'glass-card p-5 transition-all duration-200 border',
        onClick && 'cursor-pointer hover:border-console-accent/50 hover:bg-console-elevated/90 active:scale-[0.99]',
        className
      )}
    >
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-console-muted uppercase tracking-wider">{title}</p>
        {Icon && (
          <div className={clsx('p-2 rounded-lg border', getVariantStyles())}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
      <div className="mt-3 flex items-baseline">
        <p className="text-3xl font-semibold text-console-text tracking-tight font-mono">{value}</p>
      </div>
      {subtitle && <p className="mt-1 text-xs text-console-muted">{subtitle}</p>}
    </div>
  );
}
