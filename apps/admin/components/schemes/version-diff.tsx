import React from 'react';
import { EligibilityRule } from '@/types/api';
import { Plus, Minus, RefreshCw } from 'lucide-react';

interface VersionDiffProps {
  oldRules: EligibilityRule[];
  newRules: EligibilityRule[];
  oldVersionNo: number;
  newVersionNo: number;
}

export function VersionDiff({ oldRules, newRules, oldVersionNo, newVersionNo }: VersionDiffProps) {
  const oldMap = new Map(oldRules.map((r) => [r.rule_code, r]));
  const newMap = new Map(newRules.map((r) => [r.rule_code, r]));

  const added: EligibilityRule[] = [];
  const removed: EligibilityRule[] = [];
  const modified: Array<{ old: EligibilityRule; new: EligibilityRule }> = [];

  newRules.forEach((r) => {
    if (!oldMap.has(r.rule_code)) {
      added.push(r);
    } else {
      const oldR = oldMap.get(r.rule_code)!;
      if (
        oldR.field_key !== r.field_key ||
        oldR.operator !== r.operator ||
        oldR.value !== r.value ||
        oldR.mandatory !== r.mandatory
      ) {
        modified.push({ old: oldR, new: r });
      }
    }
  });

  oldRules.forEach((r) => {
    if (!newMap.has(r.rule_code)) {
      removed.push(r);
    }
  });

  return (
    <div className="glass-card p-5 space-y-4">
      <h3 className="text-xs font-semibold text-console-muted uppercase tracking-wider">
        Structured Visual Diff (v{oldVersionNo} vs v{newVersionNo})
      </h3>

      {added.length === 0 && removed.length === 0 && modified.length === 0 ? (
        <p className="text-xs text-console-muted italic">No rule discrepancies between versions.</p>
      ) : (
        <div className="space-y-3 text-xs">
          {/* Added Rules */}
          {added.map((r) => (
            <div key={r.id} className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
              <div className="flex items-center space-x-2 font-semibold">
                <Plus className="h-4 w-4 text-emerald-400" />
                <span>ADDED RULE: {r.rule_code}</span>
              </div>
              <p className="mt-1 font-mono text-[11px]">
                IF {r.field_key} {r.operator} &quot;{r.value}&quot; THEN PASS
              </p>
            </div>
          ))}

          {/* Removed Rules */}
          {removed.map((r) => (
            <div key={r.id} className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300">
              <div className="flex items-center space-x-2 font-semibold">
                <Minus className="h-4 w-4 text-red-400" />
                <span>REMOVED RULE: {r.rule_code}</span>
              </div>
              <p className="mt-1 font-mono text-[11px] line-through opacity-75">
                IF {r.field_key} {r.operator} &quot;{r.value}&quot; THEN PASS
              </p>
            </div>
          ))}

          {/* Modified Rules */}
          {modified.map((m, idx) => (
            <div key={idx} className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 space-y-1">
              <div className="flex items-center space-x-2 font-semibold">
                <RefreshCw className="h-4 w-4 text-amber-400" />
                <span>MODIFIED RULE THRESHOLD: {m.new.rule_code}</span>
              </div>
              <div className="font-mono text-[11px] grid grid-cols-2 gap-2 pt-1">
                <div className="p-2 rounded bg-console-bg/50 border border-console-border">
                  <p className="text-[10px] text-console-muted uppercase">v{oldVersionNo} (Previous)</p>
                  <p className="text-red-400">
                    {m.old.field_key} {m.old.operator} &quot;{m.old.value}&quot;
                  </p>
                </div>
                <div className="p-2 rounded bg-console-bg/50 border border-console-border">
                  <p className="text-[10px] text-console-muted uppercase">v{newVersionNo} (Proposed)</p>
                  <p className="text-emerald-400">
                    {m.new.field_key} {m.new.operator} &quot;{m.new.value}&quot;
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
