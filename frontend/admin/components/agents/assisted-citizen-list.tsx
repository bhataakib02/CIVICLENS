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
      <div className="bg-white dark:bg-slate-900/90 p-12 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl text-center space-y-3">
        <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-500 flex items-center justify-center mx-auto">
          <UserCheck className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <p className="text-base font-extrabold text-slate-900 dark:text-white">No Assisted Citizens Authorized</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
            You currently have no active consent delegated by citizens to assist with their applications.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      {citizens.map((c) => {
        const isRevoked = c.consent_status !== 'active';
        return (
          <div
            key={c.citizen_id}
            onClick={() => !isRevoked && onSelect(c)}
            className={`bg-white dark:bg-slate-900/90 p-6 rounded-3xl border transition-all duration-200 shadow-xl ${
              isRevoked
                ? 'opacity-60 bg-red-500/5 border-red-500/20 cursor-not-allowed'
                : 'border-slate-200 dark:border-slate-800 hover:border-indigo-500/50 cursor-pointer hover:-translate-y-1'
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                {isRevoked ? (
                  <ShieldAlert className="h-4 w-4 text-red-500" />
                ) : (
                  <ShieldCheck className="h-4 w-4 text-emerald-500" />
                )}
                <span className="text-xs font-bold text-slate-900 dark:text-white">
                  {c.email || c.phone_number_masked || 'Citizen Profile'}
                </span>
              </div>
              <StatusBadge status={isRevoked ? 'REVOKED' : 'ACTIVE_CONSENT'} />
            </div>

            <div className="text-xs space-y-1 font-mono text-slate-600 dark:text-slate-400">
              <p>Contact: <span className="text-slate-900 dark:text-white font-semibold">{c.phone_number_masked || '—'}</span></p>
              <p>Completeness: <span className="text-slate-900 dark:text-white font-semibold">{Math.round(c.profile_completeness * 100)}%</span></p>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs font-bold">
              <span className={isRevoked ? 'text-red-500' : 'text-indigo-600 dark:text-indigo-400'}>
                {isRevoked ? 'Access Revoked' : 'Assist Citizen'}
              </span>
              {!isRevoked && <ChevronRight className="h-4 w-4 text-indigo-500" />}
            </div>
          </div>
        );
      })}
    </div>
  );
}
