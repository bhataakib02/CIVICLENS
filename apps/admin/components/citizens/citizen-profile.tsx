import React from 'react';
import { CitizenDetail } from '@/types/api';
import { StatusBadge } from '@/components/ui/status-badge';
import { ConsentView } from './consent-view';
import { formatDate, formatCurrency } from '@/lib/formatting';

interface CitizenProfileViewProps {
  citizen: CitizenDetail;
}

export function CitizenProfileView({ citizen }: CitizenProfileViewProps) {
  const p = citizen.profile;

  return (
    <div className="space-y-6">
      {/* Overview Card */}
      <div className="glass-card p-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h2 className="text-lg font-bold text-console-text">{citizen.email || 'Citizen Account'}</h2>
            <StatusBadge status={citizen.status} />
          </div>
          <p className="text-xs text-console-muted mt-1 font-mono">
            User ID: {citizen.user_id} | Masked Phone: {citizen.phone_number_masked || 'N/A'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Snapshot */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-5 space-y-4">
            <h3 className="text-xs font-semibold text-console-muted uppercase tracking-wider">
              Profile Version Snapshot (v{p?.current_version_no || 1})
            </h3>
            {p ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
                <div>
                  <p className="text-console-muted">Date of Birth</p>
                  <p className="font-semibold text-console-text mt-0.5">{p.date_of_birth || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-console-muted">Gender</p>
                  <p className="font-semibold text-console-text capitalize mt-0.5">{p.gender || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-console-muted">Social Category</p>
                  <p className="font-semibold text-console-text uppercase mt-0.5">{p.category || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-console-muted">Occupation</p>
                  <p className="font-semibold text-console-text capitalize mt-0.5">{p.occupation || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-console-muted">Declared Annual Income</p>
                  <p className="font-semibold text-console-text mt-0.5">{formatCurrency(p.declared_annual_income)}</p>
                </div>
                <div>
                  <p className="text-console-muted">Disability Status</p>
                  <p className="font-semibold text-console-text mt-0.5">
                    {p.disability_status === true ? 'Yes' : p.disability_status === false ? 'No' : 'N/A'}
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-xs text-console-muted italic">Citizen has not completed progressive profile setup.</p>
            )}
          </div>

          {/* Activity summary */}
          <div className="glass-card p-5 grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-mono font-bold text-console-accent">{citizen.applications_count}</p>
              <p className="text-xs text-console-muted mt-1">Applications</p>
            </div>
            <div>
              <p className="text-2xl font-mono font-bold text-console-accent">{citizen.documents_count}</p>
              <p className="text-xs text-console-muted mt-1">Documents</p>
            </div>
            <div>
              <p className="text-2xl font-mono font-bold text-console-accent">{citizen.active_consents_count}</p>
              <p className="text-xs text-console-muted mt-1">Active Consents</p>
            </div>
          </div>
        </div>

        {/* Consents Card */}
        <div className="glass-card p-5 space-y-4">
          <h3 className="text-xs font-semibold text-console-muted uppercase tracking-wider">
            Consents & Authorization State
          </h3>
          <ConsentView consents={citizen.profile ? (citizen as any).consents || [] : []} />
        </div>
      </div>
    </div>
  );
}
