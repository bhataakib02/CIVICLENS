import React from 'react';
import { RuleOutcome } from '@/types/api';
import { useTranslation } from '@/lib/i18n';
import { CheckCircle2, XCircle, HelpCircle } from 'lucide-react';

interface RuleBreakdownTableProps {
  rules: RuleOutcome[];
}

export function RuleBreakdownTable({ rules }: RuleBreakdownTableProps) {
  const { t } = useTranslation();

  if (!rules || rules.length === 0) {
    return <p className="text-xs text-slate-500 italic p-3">No individual rule outcomes reported by engine.</p>;
  }

  return (
    <div className="overflow-x-auto border border-slate-200 rounded-xl bg-white">
      <table className="w-full text-left text-xs">
        <thead className="bg-slate-50 border-b border-slate-200 font-semibold text-slate-700">
          <tr>
            <th className="px-4 py-3">{t.eligibility.criterion}</th>
            <th className="px-4 py-3">{t.eligibility.ruleBreakdown}</th>
            <th className="px-4 py-3 text-center">{t.eligibility.result}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rules.map((rule, idx) => (
            <tr key={idx} className="hover:bg-slate-50/50">
              <td className="px-4 py-3 font-mono font-medium text-slate-900 capitalize">
                {rule.field_key.replace(/_/g, ' ')}
              </td>
              <td className="px-4 py-3 text-slate-600 leading-relaxed">
                {rule.explanation}
              </td>
              <td className="px-4 py-3 text-center">
                {rule.outcome === 'pass' && (
                  <span className="inline-flex items-center gap-1 font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    {t.eligibility.pass}
                  </span>
                )}
                {rule.outcome === 'fail' && (
                  <span className="inline-flex items-center gap-1 font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded">
                    <XCircle className="w-3.5 h-3.5" />
                    {t.eligibility.fail}
                  </span>
                )}
                {rule.outcome === 'unknown' && (
                  <span className="inline-flex items-center gap-1 font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                    <HelpCircle className="w-3.5 h-3.5" />
                    {t.eligibility.unknown}
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
