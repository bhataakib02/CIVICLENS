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
    info: { bg: 'bg-blue-50 border-blue-200 text-blue-800', icon: Info },
    success: { bg: 'bg-emerald-50 border-emerald-200 text-emerald-800', icon: CheckCircle2 },
    warning: { bg: 'bg-amber-50 border-amber-200 text-amber-800', icon: AlertTriangle },
    error: { bg: 'bg-rose-50 border-rose-200 text-rose-800', icon: AlertCircle }
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
