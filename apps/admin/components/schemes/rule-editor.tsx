'use client';

import React, { useState } from 'react';
import { EligibilityRule } from '@/types/api';
import { Plus, Trash2, ShieldCheck, AlertCircle } from 'lucide-react';
import { validateRules } from '@/lib/api/schemes';

interface RuleEditorProps {
  initialRules: any[];
  onSave: (rules: any[]) => void;
  disabled?: boolean;
}

const FIELD_KEYS = [
  'annual_income',
  'age',
  'state',
  'district',
  'category',
  'disability_status',
  'gender',
  'family_size',
  'occupation',
  'land_holding_acres',
];

const OPERATORS = ['==', '!=', '<=', '>=', '<', '>', 'in', 'not_in', 'is_true', 'is_false'];

export function RuleEditor({ initialRules, onSave, disabled = false }: RuleEditorProps) {
  const [rules, setRules] = useState<any[]>(
    initialRules.length > 0
      ? initialRules
      : [
          {
            rule_code: 'RULE_01',
            field_key: 'annual_income',
            operator: '<=',
            value: '250000',
            mandatory: true,
            group_id: 1,
            group_operator: 'AND',
            explanation_text: 'Annual income must be less than or equal to 2,50,000 INR.',
          },
        ]
  );
  const [validationResult, setValidationResult] = useState<{ valid: boolean; message: string } | null>(null);
  const [validating, setValidating] = useState(false);

  const handleAddRule = () => {
    const nextNum = rules.length + 1;
    setRules([
      ...rules,
      {
        rule_code: `RULE_0${nextNum}`,
        field_key: 'annual_income',
        operator: '<=',
        value: '250000',
        mandatory: true,
        group_id: 1,
        group_operator: 'AND',
        explanation_text: '',
      },
    ]);
  };

  const handleRemoveRule = (index: number) => {
    setRules(rules.filter((_, i) => i !== index));
  };

  const handleRuleChange = (index: number, key: string, val: any) => {
    const updated = [...rules];
    updated[index] = { ...updated[index], [key]: val };
    setRules(updated);
    setValidationResult(null);
  };

  const handleValidate = async () => {
    setValidating(true);
    try {
      const res = await validateRules(rules);
      setValidationResult({ valid: res.valid, message: `${res.message} (${res.normalized_rule_count} rules AST)` });
    } catch (err: any) {
      setValidationResult({ valid: false, message: err.message || 'Rule validation failed.' });
    } finally {
      setValidating(false);
    }
  };

  return (
    <div className="glass-card p-5 space-y-4">
      <div className="flex items-center justify-between border-b border-console-border pb-3">
        <div>
          <h3 className="text-xs font-semibold text-console-muted uppercase tracking-wider">
            Structured Eligibility Rule DSL Editor
          </h3>
          <p className="text-[11px] text-console-muted">
            Deterministic AST rules — Python code execution strictly prohibited per safety architecture
          </p>
        </div>
        <button onClick={handleValidate} disabled={validating || disabled} className="btn-secondary text-xs">
          {validating ? 'Validating...' : 'Validate DSL Grammar'}
        </button>
      </div>

      {validationResult && (
        <div
          className={`p-3 rounded-lg text-xs flex items-center space-x-2 ${
            validationResult.valid
              ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
              : 'bg-red-500/10 border border-red-500/30 text-red-400'
          }`}
        >
          {validationResult.valid ? <ShieldCheck className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
          <span>{validationResult.message}</span>
        </div>
      )}

      {/* Rule List */}
      <div className="space-y-3">
        {rules.map((rule, idx) => (
          <div key={idx} className="p-4 rounded-lg bg-console-bg border border-console-border space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-mono text-console-accent font-semibold">{rule.rule_code || `RULE_${idx + 1}`}</span>
              {!disabled && (
                <button
                  onClick={() => handleRemoveRule(idx)}
                  className="text-console-muted hover:text-red-400 p-1"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <div>
                <label className="block text-[10px] text-console-muted uppercase mb-1">Field Key</label>
                <select
                  disabled={disabled}
                  value={rule.field_key}
                  onChange={(e) => handleRuleChange(idx, 'field_key', e.target.value)}
                  className="input-field w-full text-xs py-1.5 font-mono"
                >
                  {FIELD_KEYS.map((k) => (
                    <option key={k} value={k}>
                      {k}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] text-console-muted uppercase mb-1">Operator</label>
                <select
                  disabled={disabled}
                  value={rule.operator}
                  onChange={(e) => handleRuleChange(idx, 'operator', e.target.value)}
                  className="input-field w-full text-xs py-1.5 font-mono"
                >
                  {OPERATORS.map((op) => (
                    <option key={op} value={op}>
                      {op}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] text-console-muted uppercase mb-1">Threshold / Value</label>
                <input
                  type="text"
                  disabled={disabled}
                  value={rule.value || ''}
                  onChange={(e) => handleRuleChange(idx, 'value', e.target.value)}
                  placeholder="e.g. 250000"
                  className="input-field w-full text-xs py-1.5 font-mono"
                />
              </div>

              <div>
                <label className="block text-[10px] text-console-muted uppercase mb-1">Mandatory?</label>
                <select
                  disabled={disabled}
                  value={rule.mandatory ? 'true' : 'false'}
                  onChange={(e) => handleRuleChange(idx, 'mandatory', e.target.value === 'true')}
                  className="input-field w-full text-xs py-1.5"
                >
                  <option value="true">Yes (Mandatory)</option>
                  <option value="false">No (Optional)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-[10px] text-console-muted uppercase mb-1">Explanation Text</label>
              <input
                type="text"
                disabled={disabled}
                value={rule.explanation_text || ''}
                onChange={(e) => handleRuleChange(idx, 'explanation_text', e.target.value)}
                placeholder="Plain-language explanation for citizens..."
                className="input-field w-full text-xs py-1.5"
              />
            </div>
          </div>
        ))}
      </div>

      {!disabled && (
        <div className="flex items-center justify-between pt-2">
          <button onClick={handleAddRule} className="btn-secondary text-xs flex items-center space-x-1.5">
            <Plus className="h-4 w-4" />
            <span>Add Rule Clause</span>
          </button>

          <button onClick={() => onSave(rules)} className="btn-primary text-xs">
            Save Rule Set
          </button>
        </div>
      )}
    </div>
  );
}
