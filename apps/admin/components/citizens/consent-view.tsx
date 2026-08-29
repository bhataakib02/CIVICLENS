import React from 'react';
import { ConsentRecord } from '@/types/api';
import { StatusBadge } from '@/components/ui/status-badge';
import { formatDate } from '@/lib/formatting';
import { ShieldCheck, ShieldAlert } from 'lucide-react';

interface ConsentViewProps {
  consents: ConsentRecord[];
}

export function ConsentView({ consents }: ConsentViewProps) {
  if (!consents || consents.length === 0) {
    return <p className="text-xs text-console-muted italic">No consent history recorded for this citizen.</p>;
  }

  return (
    <div className="space-y-3">
      {consents.map((c) => {
        const isRevoked = !!c.revoked_at;
        return (
          <div
            key={c.id}
            className={`p-4 rounded-lg border text-xs space-y-2 ${
              isRevoked
                ? 'bg-red-500/5 border-red-500/20 text-console-muted'
                : 'bg-emerald-500/5 border-emerald-500/20 text-console-text'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 font-semibold">
                {isRevoked ? (
                  <ShieldAlert className="h-4 w-4 text-red-400" />
                ) : (
                  <ShieldCheck className="h-4 w-4 text-emerald-400" />
                )}
                <span>Type: {c.consent_type}</span>
                <span className="font-mono text-[10px] text-console-muted">v{c.version}</span>
              </div>
              <StatusBadge status={isRevoked ? 'REVOKED' : 'ACTIVE'} />
            </div>

            <p className="text-console-text">
              <span className="text-console-muted">Purpose:</span> {c.purpose}
            </p>

            <div className="flex flex-wrap gap-4 text-console-muted font-mono text-[11px] pt-1 border-t border-console-border/40">
              <p>Granted: {formatDate(c.granted_at)}</p>
              {c.revoked_at && <p className="text-red-400">Revoked: {formatDate(c.revoked_at)}</p>}
              {c.agent_id && <p>Agent ID: {c.agent_id}</p>}
            </div>
          </div>
        );
      })}
    </div>
  );
}
