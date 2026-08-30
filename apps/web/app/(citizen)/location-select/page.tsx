'use client';

import React, { useState } from 'react';
import { StateDistrictSelector, LocationSelectionValue } from '@/components/ui/state-district-selector';
import { MapPin, Globe2, Building2, Layers, CheckCircle2, RefreshCw, ShieldCheck } from 'lucide-react';

export default function LocationSelectDemoPage() {
  const [selectedLocation, setSelectedLocation] = useState<LocationSelectionValue>({
    state: '',
    district: '',
    subDistrict: '',
    block: '',
    isAllDistricts: false,
    isAllSubDistricts: false,
    isAllBlocks: false
  });

  const [submittedLocation, setSubmittedLocation] = useState<LocationSelectionValue | null>(null);

  const handleComplete = (val: LocationSelectionValue) => {
    setSubmittedLocation(val);
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Page Title Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-3xl p-6 sm:p-8 text-white shadow-xl">
        <div className="flex items-center gap-3">
          <span className="bg-white/20 p-2.5 rounded-2xl backdrop-blur-md">
            <Globe2 className="w-8 h-8 text-white" />
          </span>
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              India Administrative Location Hierarchy
            </h1>
            <p className="text-blue-100 text-sm mt-1">
              Authoritative 4-Level Local Government Directory (LGD) Flow
            </p>
          </div>
        </div>

        {/* Hierarchy Badge Trail */}
        <div className="mt-6 flex flex-wrap items-center gap-2 text-xs font-semibold bg-white/10 p-3 rounded-2xl backdrop-blur-sm border border-white/10">
          <span className="bg-white/20 px-2.5 py-1 rounded-lg">1. State / Union Territory (28 States + 8 UTs)</span>
          <span>→</span>
          <span className="bg-white/20 px-2.5 py-1 rounded-lg">2. District (All Districts Option)</span>
          <span>→</span>
          <span className="bg-white/20 px-2.5 py-1 rounded-lg">3. Tehsil / Sub-District (All Tehsils)</span>
          <span>→</span>
          <span className="bg-white/20 px-2.5 py-1 rounded-lg">4. Block (All Blocks)</span>
        </div>
      </div>

      {/* Main Interactive Selector Component */}
      <StateDistrictSelector
        value={selectedLocation}
        onChange={(val) => setSelectedLocation(val)}
        onComplete={handleComplete}
      />

      {/* Live State Inspection Card */}
      <div className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2 uppercase tracking-wider">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            Live Selection & Validation Payload
          </h3>
          <span className="text-xs px-2.5 py-1 bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 font-mono font-bold rounded-lg">
            Realtime Verified
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div className="bg-white dark:bg-slate-800 p-3 rounded-xl border border-slate-200 dark:border-slate-700">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">State / UT</span>
            <strong className="text-slate-900 dark:text-white text-sm">
              {selectedLocation.state || 'None Selected'}
            </strong>
          </div>

          <div className="bg-white dark:bg-slate-800 p-3 rounded-xl border border-slate-200 dark:border-slate-700">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">District</span>
            <strong className="text-slate-900 dark:text-white text-sm">
              {selectedLocation.district || 'None Selected'}
            </strong>
            {selectedLocation.isAllDistricts && (
              <span className="block text-[10px] text-emerald-600 font-bold mt-0.5">★ Wildcard All</span>
            )}
          </div>

          <div className="bg-white dark:bg-slate-800 p-3 rounded-xl border border-slate-200 dark:border-slate-700">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Tehsil / Sub-District</span>
            <strong className="text-slate-900 dark:text-white text-sm">
              {selectedLocation.subDistrict || 'None Selected'}
            </strong>
            {selectedLocation.isAllSubDistricts && (
              <span className="block text-[10px] text-emerald-600 font-bold mt-0.5">★ Wildcard All</span>
            )}
          </div>

          <div className="bg-white dark:bg-slate-800 p-3 rounded-xl border border-slate-200 dark:border-slate-700">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Block</span>
            <strong className="text-slate-900 dark:text-white text-sm">
              {selectedLocation.block || 'None Selected'}
            </strong>
            {selectedLocation.isAllBlocks && (
              <span className="block text-[10px] text-emerald-600 font-bold mt-0.5">★ Wildcard All</span>
            )}
          </div>
        </div>

        {submittedLocation && (
          <div className="p-4 bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 rounded-xl space-y-2 text-xs">
            <div className="flex items-center gap-2 font-bold text-emerald-900 dark:text-emerald-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              Location Flow Submitted Successfully!
            </div>
            <pre className="p-2.5 bg-emerald-100/50 dark:bg-slate-900 rounded-lg text-[11px] font-mono text-slate-800 dark:text-slate-200 overflow-x-auto">
              {JSON.stringify(submittedLocation, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
