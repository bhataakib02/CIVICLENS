'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
  fetchStates,
  fetchDistrictsByState,
  fetchSubDistrictsByDistrict,
  fetchBlocksByDistrict,
  validateLocationHierarchyOnBackend,
  LocationStateItem,
  LocationDistrictItem,
  LocationSubDistrictItem,
  LocationBlockItem
} from '@/lib/api/locations';
import {
  MapPin,
  Building2,
  CheckCircle2,
  ArrowLeft,
  Search,
  RotateCcw,
  Sparkles,
  ChevronRight,
  Globe2,
  Check,
  AlertTriangle,
  Loader2,
  Layers,
  CheckCircle
} from 'lucide-react';

export interface LocationSelectionValue {
  state: string;
  district: string;
  subDistrict?: string;
  block?: string;
  isAllDistricts: boolean;
  isAllSubDistricts: boolean;
  isAllBlocks: boolean;
}

interface StateDistrictSelectorProps {
  value?: LocationSelectionValue;
  onChange?: (value: LocationSelectionValue) => void;
  onComplete?: (value: LocationSelectionValue) => void;
  className?: string;
  compact?: boolean;
}

export function StateDistrictSelector({
  value,
  onChange,
  onComplete,
  className = '',
  compact = false
}: StateDistrictSelectorProps) {
  // Wizard Step: 1 = State/UT, 2 = District, 3 = Tehsil/Sub-District, 4 = Block
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);

  // Selected Location values
  const [selectedState, setSelectedState] = useState<string>(value?.state || '');
  const [selectedDistrict, setSelectedDistrict] = useState<string>(value?.district || '');
  const [selectedSubDistrict, setSelectedSubDistrict] = useState<string>(value?.subDistrict || '');
  const [selectedBlock, setSelectedBlock] = useState<string>(value?.block || '');

  // Lists fetched dynamically
  const [states, setStates] = useState<LocationStateItem[]>([]);
  const [districts, setDistricts] = useState<LocationDistrictItem[]>([]);
  const [subDistricts, setSubDistricts] = useState<LocationSubDistrictItem[]>([]);
  const [blocks, setBlocks] = useState<LocationBlockItem[]>([]);

  // Loading & Error states
  const [loadingStates, setLoadingStates] = useState(false);
  const [loadingDistricts, setLoadingDistricts] = useState(false);
  const [loadingSubDistricts, setLoadingSubDistricts] = useState(false);
  const [loadingBlocks, setLoadingBlocks] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Search input filters per step
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<'ALL' | 'STATES' | 'UTS'>('ALL');

  // Load States on mount
  useEffect(() => {
    async function loadStates() {
      setLoadingStates(true);
      const data = await fetchStates();
      setStates(data);
      setLoadingStates(false);
    }
    loadStates();
  }, []);

  // Fetch districts when selectedState changes
  useEffect(() => {
    if (!selectedState) {
      setDistricts([]);
      return;
    }
    async function loadDistricts() {
      setLoadingDistricts(true);
      const data = await fetchDistrictsByState(selectedState);
      setDistricts(data);
      setLoadingDistricts(false);
    }
    loadDistricts();
  }, [selectedState]);

  // Fetch sub-districts when selectedDistrict changes
  useEffect(() => {
    if (!selectedDistrict || selectedDistrict === 'ALL' || selectedDistrict === 'All Districts') {
      setSubDistricts([]);
      return;
    }
    async function loadSubDistricts() {
      setLoadingSubDistricts(true);
      const data = await fetchSubDistrictsByDistrict(selectedDistrict);
      setSubDistricts(data);
      setLoadingSubDistricts(false);
    }
    loadSubDistricts();
  }, [selectedDistrict]);

  // Fetch blocks when selectedDistrict or selectedSubDistrict changes
  useEffect(() => {
    if (!selectedDistrict || selectedDistrict === 'ALL' || selectedDistrict === 'All Districts') {
      setBlocks([]);
      return;
    }
    async function loadBlocks() {
      setLoadingBlocks(true);
      const data = await fetchBlocksByDistrict(selectedDistrict, selectedSubDistrict);
      setBlocks(data);
      setLoadingBlocks(false);
    }
    loadBlocks();
  }, [selectedDistrict, selectedSubDistrict]);

  // Filtered States
  const filteredStates = useMemo(() => {
    return states.filter((st) => {
      if (typeFilter === 'STATES' && st.type !== 'STATE') return false;
      if (typeFilter === 'UTS' && st.type !== 'UNION_TERRITORY') return false;
      if (!searchQuery.trim()) return true;
      const q = searchQuery.trim().toLowerCase();
      return st.name.toLowerCase().includes(q) || st.code.toLowerCase().includes(q);
    });
  }, [states, searchQuery, typeFilter]);

  // Filtered Districts
  const filteredDistricts = useMemo(() => {
    if (!searchQuery.trim()) return districts;
    const q = searchQuery.trim().toLowerCase();
    return districts.filter((d) => d.name.toLowerCase().includes(q));
  }, [districts, searchQuery]);

  // Filtered Sub-districts
  const filteredSubDistricts = useMemo(() => {
    if (!searchQuery.trim()) return subDistricts;
    const q = searchQuery.trim().toLowerCase();
    return subDistricts.filter((sd) => sd.name.toLowerCase().includes(q));
  }, [subDistricts, searchQuery]);

  // Filtered Blocks
  const filteredBlocks = useMemo(() => {
    if (!searchQuery.trim()) return blocks;
    const q = searchQuery.trim().toLowerCase();
    return blocks.filter((b) => b.name.toLowerCase().includes(q));
  }, [blocks, searchQuery]);

  // STEP 1 HANDLER: Select State/UT
  const handleSelectState = (stateName: string) => {
    setSelectedState(stateName);
    setSelectedDistrict('');
    setSelectedSubDistrict('');
    setSelectedBlock('');
    setValidationError(null);
    setSearchQuery('');
    setStep(2); // Automatically move to Step 2 (District)
    notifyChange(stateName, '', '', '');
  };

  // STEP 2 HANDLER: Select District
  const handleSelectDistrict = async (districtName: string) => {
    setSelectedDistrict(districtName);
    setSelectedSubDistrict('');
    setSelectedBlock('');
    setValidationError(null);
    setSearchQuery('');

    // Backend parent-child validation
    const res = await validateLocationHierarchyOnBackend({
      state: selectedState,
      district: districtName
    });

    if (!res.valid) {
      setValidationError(res.error || `District '${districtName}' does not belong to '${selectedState}'`);
      return;
    }

    if (districtName === 'All Districts' || districtName === 'ALL') {
      // If "All Districts" is chosen, complete selection immediately
      const val = buildValue(selectedState, 'All Districts', 'All Tehsils', 'All Blocks');
      notifyChange(selectedState, 'All Districts', 'All Tehsils', 'All Blocks');
      if (onComplete) onComplete(val);
    } else {
      setStep(3); // Advance to Step 3 (Tehsil)
      notifyChange(selectedState, districtName, '', '');
    }
  };

  // STEP 3 HANDLER: Select Sub-District / Tehsil
  const handleSelectSubDistrict = async (subDistrictName: string) => {
    setSelectedSubDistrict(subDistrictName);
    setSelectedBlock('');
    setValidationError(null);
    setSearchQuery('');

    if (subDistrictName === 'All Tehsils' || subDistrictName === 'ALL') {
      const val = buildValue(selectedState, selectedDistrict, 'All Tehsils', 'All Blocks');
      notifyChange(selectedState, selectedDistrict, 'All Tehsils', 'All Blocks');
      if (onComplete) onComplete(val);
    } else {
      setStep(4); // Advance to Step 4 (Block)
      notifyChange(selectedState, selectedDistrict, subDistrictName, '');
    }
  };

  // STEP 4 HANDLER: Select Block / Finish
  const handleSelectBlock = (blockName: string) => {
    setSelectedBlock(blockName);
    setValidationError(null);
    const val = buildValue(selectedState, selectedDistrict, selectedSubDistrict, blockName);
    notifyChange(selectedState, selectedDistrict, selectedSubDistrict, blockName);
    if (onComplete) onComplete(val);
  };

  // Back Button Navigation Handler
  const handleBack = () => {
    setValidationError(null);
    setSearchQuery('');
    if (step === 4) {
      setSelectedBlock('');
      setStep(3);
    } else if (step === 3) {
      setSelectedSubDistrict('');
      setStep(2);
    } else if (step === 2) {
      setSelectedDistrict('');
      setStep(1);
    }
  };

  // Complete Reset Handler
  const handleReset = () => {
    setSelectedState('');
    setSelectedDistrict('');
    setSelectedSubDistrict('');
    setSelectedBlock('');
    setSearchQuery('');
    setValidationError(null);
    setStep(1);
    notifyChange('', '', '', '');
  };

  const buildValue = (st: string, dt: string, sd: string, bk: string): LocationSelectionValue => {
    const isAllDt = dt === 'All Districts' || dt === 'ALL';
    const isAllSd = sd === 'All Tehsils' || sd === 'ALL' || isAllDt;
    const isAllBk = bk === 'All Blocks' || bk === 'ALL' || isAllSd;
    return {
      state: st,
      district: dt,
      subDistrict: sd,
      block: bk,
      isAllDistricts: isAllDt,
      isAllSubDistricts: isAllSd,
      isAllBlocks: isAllBk
    };
  };

  const notifyChange = (st: string, dt: string, sd: string, bk: string) => {
    if (onChange) {
      onChange(buildValue(st, dt, sd, bk));
    }
  };

  const isAllDistricts = selectedDistrict === 'All Districts' || selectedDistrict === 'ALL';
  const isAllSubDistricts = selectedSubDistrict === 'All Tehsils' || selectedSubDistrict === 'ALL';
  const isAllBlocks = selectedBlock === 'All Blocks' || selectedBlock === 'ALL';

  return (
    <div className={`bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-6 shadow-sm ${className}`}>
      {/* Header & Step Breadcrumbs */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-100 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-400 p-1.5 rounded-lg">
              <Layers className="w-4 h-4" />
            </span>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              India Administrative Location Hierarchy
            </h3>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            LGD / IGOD Standard: State/UT → District → Tehsil/Sub-District → Block
          </p>
        </div>

        {/* Multi-step Pills */}
        <div className="flex flex-wrap items-center gap-1.5 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl text-xs font-semibold">
          <button
            type="button"
            onClick={() => setStep(1)}
            className={`px-2.5 py-1 rounded-lg transition-all ${
              step === 1
                ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm font-bold'
                : 'text-slate-500'
            }`}
          >
            1. State/UT
          </button>
          <ChevronRight className="w-3 h-3 text-slate-400" />
          <button
            type="button"
            disabled={!selectedState}
            onClick={() => selectedState && setStep(2)}
            className={`px-2.5 py-1 rounded-lg transition-all ${
              step === 2
                ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm font-bold'
                : 'text-slate-400 disabled:opacity-50'
            }`}
          >
            2. District
          </button>
          <ChevronRight className="w-3 h-3 text-slate-400" />
          <button
            type="button"
            disabled={!selectedDistrict || isAllDistricts}
            onClick={() => selectedDistrict && !isAllDistricts && setStep(3)}
            className={`px-2.5 py-1 rounded-lg transition-all ${
              step === 3
                ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm font-bold'
                : 'text-slate-400 disabled:opacity-50'
            }`}
          >
            3. Tehsil
          </button>
          <ChevronRight className="w-3 h-3 text-slate-400" />
          <button
            type="button"
            disabled={!selectedSubDistrict || isAllSubDistricts}
            onClick={() => selectedSubDistrict && !isAllSubDistricts && setStep(4)}
            className={`px-2.5 py-1 rounded-lg transition-all ${
              step === 4
                ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm font-bold'
                : 'text-slate-400 disabled:opacity-50'
            }`}
          >
            4. Block
          </button>
        </div>
      </div>

      {/* Validation Error Banner */}
      {validationError && (
        <div className="mt-4 p-3 bg-red-50 dark:bg-red-950/60 border border-red-200 dark:border-red-800 rounded-xl flex items-center gap-2 text-xs text-red-700 dark:text-red-300 font-medium">
          <AlertTriangle className="w-4 h-4 text-red-600 flex-shrink-0" />
          <span>{validationError}</span>
        </div>
      )}

      {/* STEP 1: STATE / UNION TERRITORY */}
      {step === 1 && (
        <div className="mt-4 space-y-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="relative w-full sm:flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search all 28 States & 8 Union Territories..."
                className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
              />
            </div>

            <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl text-xs font-semibold">
              <button
                type="button"
                onClick={() => setTypeFilter('ALL')}
                className={`px-2.5 py-1 rounded-lg ${typeFilter === 'ALL' ? 'bg-white dark:bg-slate-900 font-bold' : 'text-slate-500'}`}
              >
                All (36)
              </button>
              <button
                type="button"
                onClick={() => setTypeFilter('STATES')}
                className={`px-2.5 py-1 rounded-lg ${typeFilter === 'STATES' ? 'bg-white dark:bg-slate-900 font-bold' : 'text-slate-500'}`}
              >
                States (28)
              </button>
              <button
                type="button"
                onClick={() => setTypeFilter('UTS')}
                className={`px-2.5 py-1 rounded-lg ${typeFilter === 'UTS' ? 'bg-white dark:bg-slate-900 font-bold' : 'text-slate-500'}`}
              >
                UTs (8)
              </button>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
              Select State / Union Territory:
            </label>
            {loadingStates ? (
              <div className="py-4 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" /> Loading authoritative LGD State list...
              </div>
            ) : (
              <select
                value={selectedState}
                onChange={(e) => e.target.value && handleSelectState(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-semibold text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Choose State or Union Territory --</option>
                <optgroup label="28 States of India">
                  {states.filter((s) => s.type === 'STATE').map((s) => (
                    <option key={s.code} value={s.name}>{s.name}</option>
                  ))}
                </optgroup>
                <optgroup label="8 Union Territories">
                  {states.filter((s) => s.type === 'UNION_TERRITORY').map((s) => (
                    <option key={s.code} value={s.name}>{s.name} (UT)</option>
                  ))}
                </optgroup>
              </select>
            )}
          </div>

          {!compact && (
            <div className="max-h-60 overflow-y-auto pr-1 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 border border-slate-100 dark:border-slate-800 rounded-xl p-2 bg-slate-50/50 dark:bg-slate-900/50">
              {filteredStates.map((st) => (
                <button
                  key={st.code}
                  type="button"
                  onClick={() => handleSelectState(st.name)}
                  className={`flex items-center justify-between p-2.5 rounded-xl border text-left text-xs transition-all ${
                    selectedState === st.name
                      ? 'bg-blue-600 text-white border-blue-600 font-bold shadow-sm'
                      : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border-slate-200 dark:border-slate-700 hover:border-blue-400'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <Building2 className="w-3.5 h-3.5 flex-shrink-0 text-blue-500" />
                    <span className="truncate">{st.name}</span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 bg-slate-100 dark:bg-slate-700 rounded font-mono">
                    {st.type === 'UNION_TERRITORY' ? 'UT' : 'STATE'}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* STEP 2: DISTRICT SELECTION */}
      {step === 2 && (
        <div className="mt-4 space-y-4">
          <div className="flex items-center justify-between bg-blue-50 dark:bg-blue-950/60 p-3 rounded-xl border border-blue-200 dark:border-blue-800">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleBack}
                className="flex items-center gap-1 px-2.5 py-1 bg-white dark:bg-slate-800 text-blue-700 dark:text-blue-300 text-xs font-bold rounded-lg border border-blue-300 dark:border-blue-700"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back
              </button>
              <span className="text-xs">
                State/UT: <strong className="text-blue-900 dark:text-blue-200 font-bold">{selectedState}</strong>
              </span>
            </div>
            <button type="button" onClick={handleReset} className="text-[11px] text-slate-500 hover:text-red-600 flex items-center gap-1">
              <RotateCcw className="w-3 h-3" /> Change State
            </button>
          </div>

          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={`Search districts in ${selectedState}...`}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
              Select District:
            </label>
            {loadingDistricts ? (
              <div className="py-4 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" /> Loading official districts...
              </div>
            ) : (
              <select
                value={selectedDistrict}
                onChange={(e) => e.target.value && handleSelectDistrict(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-semibold text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Choose District --</option>
                <option value="All Districts" className="font-bold text-blue-600 bg-blue-50">
                  ★ All Districts (Entire {selectedState})
                </option>
                {districts.map((d) => (
                  <option key={d.code} value={d.name}>{d.name} District</option>
                ))}
              </select>
            )}
          </div>

          {/* District Grid */}
          <div className="max-h-56 overflow-y-auto pr-1 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 border border-slate-100 dark:border-slate-800 rounded-xl p-2 bg-slate-50/50 dark:bg-slate-900/50">
            <button
              type="button"
              onClick={() => handleSelectDistrict('All Districts')}
              className={`col-span-full flex items-center justify-between p-2.5 rounded-xl border text-xs font-bold transition-all ${
                isAllDistricts
                  ? 'bg-emerald-600 text-white border-emerald-600 shadow-md'
                  : 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-900 dark:text-emerald-300 border-emerald-200'
              }`}
            >
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                <span>All Districts (Entire {selectedState})</span>
              </div>
              {isAllDistricts && <Check className="w-4 h-4" />}
            </button>

            {filteredDistricts.map((d) => (
              <button
                key={d.code}
                type="button"
                onClick={() => handleSelectDistrict(d.name)}
                className={`flex items-center justify-between p-2.5 rounded-xl border text-left text-xs transition-all ${
                  selectedDistrict === d.name
                    ? 'bg-blue-600 text-white border-blue-600 font-bold'
                    : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border-slate-200 dark:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <MapPin className="w-3.5 h-3.5 flex-shrink-0 text-slate-400" />
                  <span className="truncate">{d.name}</span>
                </div>
                {selectedDistrict === d.name && <Check className="w-3.5 h-3.5 text-white" />}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* STEP 3: TEHSIL / SUB-DISTRICT */}
      {step === 3 && (
        <div className="mt-4 space-y-4">
          <div className="flex items-center justify-between bg-blue-50 dark:bg-blue-950/60 p-3 rounded-xl border border-blue-200 dark:border-blue-800">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleBack}
                className="flex items-center gap-1 px-2.5 py-1 bg-white dark:bg-slate-800 text-blue-700 dark:text-blue-300 text-xs font-bold rounded-lg border border-blue-300 dark:border-blue-700"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back
              </button>
              <span className="text-xs">
                State: <strong>{selectedState}</strong> / District: <strong className="text-blue-900 dark:text-blue-200 font-bold">{selectedDistrict}</strong>
              </span>
            </div>
            <button type="button" onClick={handleReset} className="text-[11px] text-slate-500 hover:text-red-600 flex items-center gap-1">
              <RotateCcw className="w-3 h-3" /> Reset
            </button>
          </div>

          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={`Search tehsils / taluks in ${selectedDistrict}...`}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
              Select Tehsil / Sub-District / Taluk / Mandal:
            </label>
            {loadingSubDistricts ? (
              <div className="py-4 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" /> Loading tehsils / sub-districts...
              </div>
            ) : (
              <select
                value={selectedSubDistrict}
                onChange={(e) => e.target.value && handleSelectSubDistrict(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-semibold text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Choose Tehsil / Sub-District --</option>
                <option value="All Tehsils" className="font-bold text-blue-600 bg-blue-50">
                  ★ All Tehsils (Entire {selectedDistrict} District)
                </option>
                {subDistricts.map((sd) => (
                  <option key={sd.code} value={sd.name}>{sd.official_name || sd.name}</option>
                ))}
              </select>
            )}
          </div>

          {/* Sub-district Grid */}
          <div className="max-h-56 overflow-y-auto pr-1 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 border border-slate-100 dark:border-slate-800 rounded-xl p-2 bg-slate-50/50 dark:bg-slate-900/50">
            <button
              type="button"
              onClick={() => handleSelectSubDistrict('All Tehsils')}
              className={`col-span-full flex items-center justify-between p-2.5 rounded-xl border text-xs font-bold transition-all ${
                isAllSubDistricts
                  ? 'bg-emerald-600 text-white border-emerald-600 shadow-md'
                  : 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-900 dark:text-emerald-300 border-emerald-200'
              }`}
            >
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                <span>All Tehsils (Entire {selectedDistrict} District)</span>
              </div>
              {isAllSubDistricts && <Check className="w-4 h-4" />}
            </button>

            {filteredSubDistricts.map((sd) => (
              <button
                key={sd.code}
                type="button"
                onClick={() => handleSelectSubDistrict(sd.name)}
                className={`flex items-center justify-between p-2.5 rounded-xl border text-left text-xs transition-all ${
                  selectedSubDistrict === sd.name
                    ? 'bg-blue-600 text-white border-blue-600 font-bold'
                    : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border-slate-200 dark:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <Building2 className="w-3.5 h-3.5 flex-shrink-0 text-slate-400" />
                  <span className="truncate">{sd.name}</span>
                </div>
                {selectedSubDistrict === sd.name && <Check className="w-3.5 h-3.5 text-white" />}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* STEP 4: BLOCK SELECTION */}
      {step === 4 && (
        <div className="mt-4 space-y-4">
          <div className="flex items-center justify-between bg-blue-50 dark:bg-blue-950/60 p-3 rounded-xl border border-blue-200 dark:border-blue-800">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleBack}
                className="flex items-center gap-1 px-2.5 py-1 bg-white dark:bg-slate-800 text-blue-700 dark:text-blue-300 text-xs font-bold rounded-lg border border-blue-300 dark:border-blue-700"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back
              </button>
              <span className="text-xs">
                District: <strong>{selectedDistrict}</strong> / Tehsil: <strong className="text-blue-900 dark:text-blue-200 font-bold">{selectedSubDistrict}</strong>
              </span>
            </div>
            <button type="button" onClick={handleReset} className="text-[11px] text-slate-500 hover:text-red-600 flex items-center gap-1">
              <RotateCcw className="w-3 h-3" /> Reset
            </button>
          </div>

          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={`Search blocks in ${selectedSubDistrict}...`}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
              Select Community Development Block:
            </label>
            {loadingBlocks ? (
              <div className="py-4 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" /> Loading blocks...
              </div>
            ) : (
              <select
                value={selectedBlock}
                onChange={(e) => e.target.value && handleSelectBlock(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-semibold text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Choose CD Block --</option>
                <option value="All Blocks" className="font-bold text-blue-600 bg-blue-50">
                  ★ All Blocks (Entire {selectedSubDistrict})
                </option>
                {blocks.map((b) => (
                  <option key={b.code} value={b.name}>{b.official_name || b.name}</option>
                ))}
              </select>
            )}
          </div>

          {/* Block Grid */}
          <div className="max-h-56 overflow-y-auto pr-1 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 border border-slate-100 dark:border-slate-800 rounded-xl p-2 bg-slate-50/50 dark:bg-slate-900/50">
            <button
              type="button"
              onClick={() => handleSelectBlock('All Blocks')}
              className={`col-span-full flex items-center justify-between p-2.5 rounded-xl border text-xs font-bold transition-all ${
                isAllBlocks
                  ? 'bg-emerald-600 text-white border-emerald-600 shadow-md'
                  : 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-900 dark:text-emerald-300 border-emerald-200'
              }`}
            >
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                <span>All Blocks (Entire {selectedSubDistrict})</span>
              </div>
              {isAllBlocks && <Check className="w-4 h-4" />}
            </button>

            {filteredBlocks.map((b) => (
              <button
                key={b.code}
                type="button"
                onClick={() => handleSelectBlock(b.name)}
                className={`flex items-center justify-between p-2.5 rounded-xl border text-left text-xs transition-all ${
                  selectedBlock === b.name
                    ? 'bg-blue-600 text-white border-blue-600 font-bold'
                    : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border-slate-200 dark:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <MapPin className="w-3.5 h-3.5 flex-shrink-0 text-slate-400" />
                  <span className="truncate">{b.name}</span>
                </div>
                {selectedBlock === b.name && <Check className="w-3.5 h-3.5 text-white" />}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Confirmation & Summary Footer */}
      {selectedState && (
        <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300 font-medium">
            <CheckCircle className="w-4 h-4 text-emerald-500" />
            <span>
              Hierarchy: <strong>{selectedState}</strong>
              {selectedDistrict && <> → <strong>{selectedDistrict}</strong></>}
              {selectedSubDistrict && <> → <strong>{selectedSubDistrict}</strong></>}
              {selectedBlock && <> → <strong>{selectedBlock}</strong></>}
            </span>
          </div>

          <button
            type="button"
            onClick={handleReset}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 underline"
          >
            Clear Selection
          </button>
        </div>
      )}
    </div>
  );
}
