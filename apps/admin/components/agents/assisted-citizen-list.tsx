import React from 'react';
import { AssistedCitizen } from '@/types/api';
import { StatusBadge } from '@/components/ui/status-badge';
import { ShieldCheck, ShieldAlert, ChevronRight, UserCheck } from 'lucide-react';

interface AssistedCitizenListProps {
  citizens: AssistedCitizen[];
  onSelect: (citizen: AssistedCitizen) => void;
}

export function AssistedCitizenList({ citizens, onSelect }: AssistedCitizenListProps) {
  if (!citizens || citizens.length === 0) {
    return (
      <div className="glass-card p-8 text-center text-console-muted">
        <UserCheck className="h-8 w-8 mx-auto mb-2 text-console-muted/50" />
        <p className="text-sm font-medium text-console-text">No Assisted Citizens Authorized</p>
        <p className="text-xs mt-1">
          You currently have no active consent delegated by citizens to assist with their applications.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {citizens.map((c) => {
        const isRevoked = c.consent_status !== 'active';
        return (
          <div
            key={c.citizen_id}
            onClick={() => !isRevoked && onSelect(c)}
            className={`glass-card p-5 border transition-all duration-200 ${
              isRevoked
                ? 'opacity-60 bg-red-500/5 border-red-500/20 cursor-not-allowed'
                : 'hover:border-console-accent/50 cursor-pointer hover:scale-[1.01]'
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                {isRevoked ? (
                  <ShieldAlert className="h-4 w-4 text-red-400" />
                ) : (
                  <ShieldCheck className="h-4 w-4 text-emerald-400" />
                )}
                <span className="text-xs font-semibold text-console-text">
                  {c.email || c.phone_number_masked || 'Citizen Profile'}
                </span>
              </div>
              <StatusBadge status={isRevoked ? 'REVOKED' : 'ACTIVE_CONSENT'} />
            </div>

            <div className="text-xs space-y-1 font-mono text-console-muted">
              <p>Masked Contact: {c.phone_number_masked || '—'}</p>
              <p>Completeness: {Math.round(c.profile_completeness * 100)}%</p>
            </div>

            <div className="mt-4 pt-3 border-t border-console-border/40 flex items-center justify-between text-xs">
              <span className={isRevoked ? 'text-red-400 font-medium' : 'text-console-accent font-medium'}>
                {isRevoked ? 'Access Revoked' : 'Assist Citizen'}
              </span>
              {!isRevoked && <ChevronRight className="h-4 w-4 text-console-accent" />}
            </div>
          </div>
        );
      })}
    </div>
  );
}
