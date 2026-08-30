import React from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle } from 'lucide-react';

interface AlertProps {
  type?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function Alert({ type = 'info', title, children, className = '' }: AlertProps) {
  const styles = {
    info: { bg: 'bg-blue-950/50 border-blue-800 text-blue-200', icon: Info },
    success: { bg: 'bg-emerald-950/50 border-emerald-800 text-emerald-200', icon: CheckCircle2 },
    warning: { bg: 'bg-amber-950/50 border-amber-800 text-amber-200', icon: AlertTriangle },
    error: { bg: 'bg-rose-950/50 border-rose-800 text-rose-200', icon: AlertCircle }
  };

  const currentStyle = styles[type];
  const IconComponent = currentStyle.icon;

  return (
    <div className={`p-4 rounded-xl border flex items-start gap-3 ${currentStyle.bg} ${className}`} role="alert">
      <IconComponent className="w-5 h-5 flex-shrink-0 mt-0.5" />
      <div className="text-sm">
        {title && <h4 className="font-semibold mb-1">{title}</h4>}
        <div>{children}</div>
      </div>
    </div>
  );
}
